import pandas as pd
import numpy as np
from rich.console import Console
from rich.table import Table
from rich import box

def run_ensemble(ticker, valuation_results, lstm_mean, sentiment_agg):
    """
    Combine three independent signals into one investment recommendation.

    Signals:
    1. Fundamental valuation (DCF + EV/EBITDA + P/E) — weight 50%
    2. LSTM forecast vs manual projection divergence  — weight 25%
    3. FinBERT sentiment score                        — weight 25%

    Each signal produces a score from -1 (very bearish) to +1 (very bullish).
    Weighted average → final score → rating + confidence.
    """
    from src.data.fetch import get_company_info
    info    = get_company_info(ticker)
    current = info.get("current_price") or 1000

    # ── Signal 1: Valuation signal ───────────────────────────────────────────
    # Use base case weighted target vs current price
    try:
        base_target = float(valuation_results.loc["📊 Base", "Weighted (₹)"])
        upside      = (base_target - current) / current
        # Normalise: +30% upside → +1.0, -30% → -1.0
        val_score   = max(-1.0, min(1.0, upside / 0.30))
    except:
        val_score = 0.0

    # ── Signal 2: LSTM signal ────────────────────────────────────────────────
    # Compare LSTM annual PAT forecast vs manual base case PAT
    try:
        manual_pat  = None
        # Get manual base case PAT FY2026E
        from src.financial.scenarios import run_scenario
        df_base     = run_scenario(ticker, "📊 Base")
        manual_pat  = df_base.loc["FY2026E", "PAT"]

        if lstm_mean is not None and manual_pat and manual_pat > 0:
            lstm_annual = sum(lstm_mean)
            divergence  = (lstm_annual - manual_pat) / manual_pat
            # Positive divergence = ML more optimistic = bullish signal
            lstm_score  = max(-1.0, min(1.0, divergence / 0.30))
        else:
            lstm_score  = 0.0  # neutral if no LSTM data
    except:
        lstm_score = 0.0

    # ── Signal 3: Sentiment signal ───────────────────────────────────────────
    try:
        avg_score    = sentiment_agg["avg_score"] if sentiment_agg else 0
        # FinBERT compound already -1 to +1, scale to our range
        sent_score   = max(-1.0, min(1.0, avg_score))
    except:
        sent_score = 0.0

    # ── Weighted ensemble ────────────────────────────────────────────────────
    weights       = {"valuation": 0.50, "lstm": 0.25, "sentiment": 0.25}
    ensemble_score = (
        val_score  * weights["valuation"] +
        lstm_score * weights["lstm"]      +
        sent_score * weights["sentiment"]
    )
    ensemble_score = round(ensemble_score, 3)

    # ── Rating ───────────────────────────────────────────────────────────────
    if ensemble_score >= 0.3:
        rating      = "✅ STRONG BUY"
        color       = "bold green"
        confidence  = "High"
    elif ensemble_score >= 0.1:
        rating      = "✅ BUY"
        color       = "green"
        confidence  = "Moderate"
    elif ensemble_score >= -0.1:
        rating      = "⚪ HOLD"
        color       = "yellow"
        confidence  = "Low"
    elif ensemble_score >= -0.3:
        rating      = "🔴 SELL"
        color       = "red"
        confidence  = "Moderate"
    else:
        rating      = "🔴 STRONG SELL"
        color       = "bold red"
        confidence  = "High"

    return {
        "val_score":      round(val_score, 3),
        "lstm_score":     round(lstm_score, 3),
        "sent_score":     round(sent_score, 3),
        "ensemble_score": ensemble_score,
        "rating":         rating,
        "color":          color,
        "confidence":     confidence,
        "weights":        weights,
    }


def print_ensemble(ticker, valuation_results, lstm_mean, sentiment_agg):
    console = Console()
    result  = run_ensemble(ticker, valuation_results, lstm_mean, sentiment_agg)

    console.print("\n[bold white]━━━ Ensemble Signal ━━━[/bold white]")
    console.print(f"[dim]Combining 3 independent signals with weighted voting[/dim]\n")

    # Signal breakdown table
    t = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE_HEAVY)
    t.add_column("Signal",      style="cyan", width=20)
    t.add_column("Score",       justify="right", width=10)
    t.add_column("Weight",      justify="right", width=10)
    t.add_column("Contribution",justify="right", width=14)
    t.add_column("Basis",       width=30)

    signals = [
        ("Fundamental (DCF)",
         result["val_score"],
         result["weights"]["valuation"],
         "Base case target vs CMP"),
        ("LSTM Forecast",
         result["lstm_score"],
         result["weights"]["lstm"],
         "ML PAT vs manual projection"),
        ("FinBERT Sentiment",
         result["sent_score"],
         result["weights"]["sentiment"],
         "News flow score"),
    ]

    for name, score, weight, basis in signals:
        contrib = score * weight
        color   = "green" if score > 0.1 else "red" if score < -0.1 else "yellow"
        t.add_row(
            name,
            f"[{color}]{score:+.3f}[/{color}]",
            f"{weight:.0%}",
            f"[{color}]{contrib:+.3f}[/{color}]",
            basis,
        )
    console.print(t)

    # Score bar
    bar_len   = 30
    zero_pos  = bar_len // 2
    score_pos = int(zero_pos + result["ensemble_score"] * zero_pos)
    score_pos = max(0, min(bar_len - 1, score_pos))
    bar       = ["─"] * bar_len
    bar[zero_pos]  = "│"
    bar[score_pos] = "●"
    bar_str   = "".join(bar)

    console.print(f"\n  Bearish  [{bar_str}]  Bullish")
    console.print(f"           -1.0{'':>12}0{'':>12}+1.0\n")

    # Final verdict
    console.print(f"  Ensemble Score : [{result['color']}]{result['ensemble_score']:+.3f}[/{result['color']}]")
    console.print(f"  Rating         : [{result['color']}]{result['rating']}[/{result['color']}]")
    console.print(f"  Confidence     : {result['confidence']}")
    console.print(f"\n  [dim]Signal weights: Valuation 50% · LSTM 25% · Sentiment 25%[/dim]")
    console.print(f"  [dim]Score range: -1.0 (strong sell) to +1.0 (strong buy)[/dim]\n")