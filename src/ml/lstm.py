import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error
from rich.console import Console
from rich.table import Table
from rich import box
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")

DEVICE     = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SEQ_LEN    = 3   # input: last 4 quarters
PRED_LEN   = 3   # output: next 4 quarters (1 year)
HIDDEN     = 64
LAYERS     = 2
DROPOUT    = 0.2
EPOCHS     = 300
LR         = 0.001
MC_SAMPLES = 100  # Monte Carlo dropout samples for confidence intervals

# ── Features used for LSTM input ────────────────────────────────────────────
FEATURES = ["revenue", "gross_profit", "operating_income", "net_income"]
TARGET   = "net_income"  # what we're forecasting

# ── Data fetching ────────────────────────────────────────────────────────────

def fetch_quarterly_data(ticker):
    import yfinance as yf
    t    = yf.Ticker(ticker)
    info = t.info

    # Detect USD disguised as INR
    market_cap_cr = (info.get("marketCap") or 0) / 1e7
    currency      = info.get("currency", "INR")

    inc = t.quarterly_financials
    use_annual = False

    if inc is None or inc.empty or len(inc.columns) < 4:
        inc        = t.financials
        use_annual = True

    if inc is None or inc.empty:
        return None

    # Check USD flag using P/S ratio
    usd_flag = False
    if "Total Revenue" in inc.index:
        try:
            raw_rev    = float(inc.loc["Total Revenue"].iloc[0])
            rev_cr_inr = raw_rev / 1e7
            ps_ratio   = market_cap_cr / rev_cr_inr if rev_cr_inr > 0 else 999
            if ps_ratio > 20:
                usd_flag = True
        except:
            pass

    fx = 85.0 if usd_flag else 1.0

    rows = []
    for col in reversed(inc.columns):
        def safe(key, col=col):
            try:    return float(inc.loc[key, col]) * fx / 1e7
            except: return np.nan

        rows.append({
            "date":             col,
            "revenue":          safe("Total Revenue"),
            "gross_profit":     safe("Gross Profit"),
            "operating_income": safe("Operating Income"),
            "net_income":       safe("Net Income"),
        })

    df = pd.DataFrame(rows).set_index("date")
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.ffill().bfill()
    df = df.dropna()

    if use_annual and len(df) >= 3:
        df_interp = df.resample('QE').interpolate(method='linear')
        return df_interp

    return df

def augment_data(df, n_augments=3):
    """
    Augment small dataset with slight noise — standard technique
    for financial time series with limited history.
    """
    augmented = [df.copy()]
    for _ in range(n_augments):
        noise = df * (1 + np.random.normal(0, 0.02, df.shape))
        augmented.append(noise)
    return pd.concat(augmented, ignore_index=True)


# ── LSTM Model ───────────────────────────────────────────────────────────────

class FinancialLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers,
                 output_size, dropout):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size  = input_size,
            hidden_size = hidden_size,
            num_layers  = num_layers,
            dropout     = dropout if num_layers > 1 else 0,
            batch_first = True,
        )
        self.dropout = nn.Dropout(dropout)  # MC Dropout
        self.fc      = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        out, _ = self.lstm(x)
        out     = self.dropout(out[:, -1, :])  # last timestep
        return self.fc(out)


# ── Sequence builder ─────────────────────────────────────────────────────────

def build_sequences(data, seq_len, pred_len):
    X, y = [], []
    for i in range(len(data) - seq_len - pred_len + 1):
        X.append(data[i : i + seq_len])
        y.append(data[i + seq_len : i + seq_len + pred_len, -1])  # target col
    return np.array(X), np.array(y)


# ── Training ─────────────────────────────────────────────────────────────────

def train_model(X_train, y_train):
    model     = FinancialLSTM(
        input_size  = X_train.shape[2],
        hidden_size = HIDDEN,
        num_layers  = LAYERS,
        output_size = PRED_LEN,
        dropout     = DROPOUT,
    ).to(DEVICE)

    optimiser = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.MSELoss()
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimiser, patience=30, factor=0.5
    )

    X_t = torch.FloatTensor(X_train).to(DEVICE)
    y_t = torch.FloatTensor(y_train).to(DEVICE)

    model.train()
    best_loss = float("inf")
    best_state = None

    for epoch in range(EPOCHS):
        optimiser.zero_grad()
        pred = model(X_t)
        loss = criterion(pred, y_t)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimiser.step()
        scheduler.step(loss)

        if loss.item() < best_loss:
            best_loss  = loss.item()
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)
    return model


# ── Monte Carlo prediction ────────────────────────────────────────────────────

def mc_predict(model, X_input, n_samples=MC_SAMPLES):
    """
    Run forward pass n_samples times with dropout ON.
    Mean = point estimate. Std = uncertainty.
    This gives confidence intervals without a separate model.
    """
    model.train()  # keep dropout active
    preds = []
    X_t   = torch.FloatTensor(X_input).to(DEVICE)

    with torch.no_grad():
        for _ in range(n_samples):
            pred = model(X_t).cpu().numpy()
            preds.append(pred)

    preds  = np.array(preds)         # (n_samples, batch, pred_len)
    mean   = preds.mean(axis=0)      # (batch, pred_len)
    std    = preds.std(axis=0)       # (batch, pred_len)
    return mean, std


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_lstm_forecast(ticker):
    console = Console()

    # 1. Fetch data
    df = fetch_quarterly_data(ticker)
    if df is None or len(df) < SEQ_LEN + PRED_LEN:
        return None, None, None, f"Insufficient data ({len(df) if df is not None else 0} quarters)"

    # 2. Scale
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df[FEATURES].values)

    # 3. Augment if small dataset
    if len(scaled) < 20:
        df_aug = pd.DataFrame(scaled, columns=FEATURES)
        df_aug = augment_data(df_aug, n_augments=4)
        scaled_aug = df_aug.values
    else:
        scaled_aug = scaled

    # 4. Build sequences
    X, y = build_sequences(scaled_aug, SEQ_LEN, PRED_LEN)
    if len(X) < 2:
        return None, None, None, "Not enough sequences to train"

    # 5. Train
    model = train_model(X, y)

    # 6. Predict on last SEQ_LEN quarters
    last_seq = scaled[-SEQ_LEN:].reshape(1, SEQ_LEN, len(FEATURES))
    mean_scaled, std_scaled = mc_predict(model, last_seq)

    # 7. Inverse transform — reconstruct full feature array to invert
    def inverse_target(vals_scaled):
        dummy = np.zeros((len(vals_scaled), len(FEATURES)))
        dummy[:, FEATURES.index(TARGET)] = vals_scaled
        return scaler.inverse_transform(dummy)[:, FEATURES.index(TARGET)]

    mean_pred = inverse_target(mean_scaled[0])
    upper     = inverse_target(mean_scaled[0] + std_scaled[0])
    lower     = inverse_target(mean_scaled[0] - std_scaled[0])

    # 8. Compute MAE on training set
    train_preds, _ = mc_predict(model, X)
    y_true = inverse_target(y[:, -1])
    y_hat  = inverse_target(train_preds[:, -1])
    mae    = mean_absolute_error(y_true, y_hat)

    return mean_pred, lower, upper, mae


def print_ml_forecast(ticker):
    console = Console()
    console.print(f"\n[bold blue]━━━ LSTM Financial Forecast ━━━[/bold blue]")
    console.print(f"[dim]Training on quarterly data for {ticker}...[/dim]")
    console.print(f"[dim]Device: {DEVICE} | Seq len: {SEQ_LEN}Q → Pred: {PRED_LEN}Q[/dim]\n")

    mean, lower, upper, mae_or_err = run_lstm_forecast(ticker)

    if mean is None:
        console.print(f"[red]LSTM skipped: {mae_or_err}[/red]")
        return

    quarters = ["Q1 FY26E", "Q2 FY26E", "Q3 FY26E"][:PRED_LEN]
    t = Table(show_header=True, header_style="bold magenta", box=box.HEAVY_EDGE)
    t.add_column("Quarter",          width=12)
    t.add_column("Forecast PAT",     justify="right", width=16)
    t.add_column("Lower (–1σ)",      justify="right", width=14)
    t.add_column("Upper (+1σ)",      justify="right", width=14)
    t.add_column("Confidence Range", justify="right", width=18)

    for i, q in enumerate(quarters):
        m = mean[i]; l = lower[i]; u = upper[i]
        rng = u - l
        t.add_row(
            q,
            f"[green]₹{m:,.0f} cr[/green]",
            f"₹{l:,.0f} cr",
            f"₹{u:,.0f} cr",
            f"± ₹{rng/2:,.0f} cr",
        )
    console.print(t)

    annual_pat = sum(mean)
    console.print(f"\n  [cyan]Annual PAT FY2026E (sum of 4Q)[/cyan]: "
                  f"[bold green]₹{annual_pat:,.0f} cr[/bold green]")
    console.print(f"  [cyan]Training MAE[/cyan]: ₹{mae_or_err:,.0f} cr")
    console.print(f"\n  [dim]Confidence intervals via Monte Carlo Dropout "
                  f"({MC_SAMPLES} forward passes)[/dim]")
    console.print(f"  [dim]Model: {LAYERS}-layer LSTM · "
                  f"Hidden: {HIDDEN} · Dropout: {DROPOUT}[/dim]\n")


if __name__ == "__main__":
    print_ml_forecast("RELIANCE.NS")