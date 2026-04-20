import pandas as pd
import numpy as np
from rich.console import Console
from rich.table import Table
from src.data.fetch import get_company_info, get_financials
from src.financial.templates import get_template

PROJ_YEARS = ["FY2025E", "FY2026E", "FY2027E"]

def get_base_financials(ticker):
    info = get_company_info(ticker)
    fins = get_financials(ticker)
    inc  = fins["income"]
    bal  = fins["balance"]
    csh  = fins["cashflow"]

    # ── Detect USD disguised as INR ──────────────────────────────────────
    # yfinance returns revenue/ebitda in USD for some NSE stocks (e.g. INFY)
    # Detection: if P/S ratio using raw÷1e7 is > 20x, data is in USD
    usd_flag = False
    market_cap_cr = info.get("market_cap_cr") or 0
    if inc is not None and "Total Revenue" in inc.index:
        try:
            raw_rev     = float(inc.loc["Total Revenue"].iloc[0])
            rev_cr_inr  = raw_rev / 1e7
            ps_ratio    = market_cap_cr / rev_cr_inr if rev_cr_inr > 0 else 999
            if ps_ratio > 20:   # unrealistic P/S → data must be USD
                usd_flag = True
        except:
            pass

    fx = 85.0 if usd_flag else 1.0

    def safe(df, key, col=0):
        try:
            return round(float(df.loc[key].iloc[col]) * fx / 1e7, 0)
        except:
            return None

    revenue      = safe(inc, "Total Revenue")
    gross_profit = safe(inc, "Gross Profit")
    ebitda       = safe(inc, "Normalized EBITDA") or safe(inc, "EBITDA")
    ebit         = safe(inc, "EBIT") or safe(inc, "Operating Income")
    pat          = safe(inc, "Net Income")
    depreciation = safe(csh, "Depreciation And Amortization")
    capex        = abs(safe(csh, "Capital Expenditure") or 0)
    total_debt   = safe(bal, "Total Debt") or 0
    cash         = safe(bal, "Cash And Cash Equivalents") or 0
    equity       = safe(bal, "Stockholders Equity")

    # fallback: use info fields if statements missing
    if not revenue or revenue < 100:
        revenue = info.get("revenue_cr") or 100000
    if not ebitda or ebitda < 10:
        ebitda = info.get("ebitda_cr") or revenue * 0.15

    return {
        "revenue":      revenue,
        "gross_profit": gross_profit,
        "ebitda":       ebitda,
        "ebit":         ebit,
        "pat":          pat,
        "depreciation": depreciation,
        "capex":        capex,
        "total_debt":   total_debt,
        "cash":         cash,
        "total_assets": safe(bal, "Total Assets"),
        "equity":       equity,
        "shares_cr":    info.get("shares_cr"),
        "sector":       info.get("sector", "Unknown"),
        "name":         info.get("name", ticker),
        "usd_flag":     usd_flag,  # useful for debugging
    }

def project_financials(ticker):
    base = get_base_financials(ticker)
    tmpl = get_template(base["sector"])

    revenue     = base["revenue"]   or 100000
    ebitda      = base["ebitda"]    or revenue * tmpl["ebitda_margin"][0]
    pat         = base["pat"]       or ebitda * 0.5
    depreciation= base["depreciation"] or revenue * 0.04
    capex       = base["capex"]     or revenue * tmpl["capex_pct_rev"]
    total_debt  = base["total_debt"] or 0
    cash        = base["cash"]      or 0
    equity      = base["equity"]    or revenue * 0.5

    rows = []
    prev = {
        "revenue": revenue, "ebitda": ebitda, "pat": pat,
        "depreciation": depreciation, "capex": capex,
        "total_debt": total_debt, "cash": cash, "equity": equity,
    }

    for i, yr in enumerate(PROJ_YEARS):
        rev   = prev["revenue"]  * (1 + tmpl["revenue_growth"][i])
        ebitda_new = rev * tmpl["ebitda_margin"][i]
        dep   = rev * 0.04
        ebit  = ebitda_new - dep
        capex_new = rev * tmpl["capex_pct_rev"]
        wc_change = rev * tmpl["wc_pct_rev"] * 0.1
        tax   = ebit * tmpl["tax_rate"]
        pat_new = ebit - tax - (prev["total_debt"] * 0.07)
        pat_new = max(pat_new, 0)

        # Free Cash Flow = EBITDA - Tax - Capex - WC change
        fcf = ebitda_new - tax - capex_new - wc_change

        # Net debt
        net_debt = prev["total_debt"] - prev["cash"]
        equity_new = prev["equity"] + pat_new * 0.70

        eps = pat_new / base["shares_cr"] if base["shares_cr"] else 0

        rows.append({
            "Year":          yr,
            "Revenue":       round(rev),
            "EBITDA":        round(ebitda_new),
            "EBITDA Margin": round(ebitda_new / rev * 100, 1),
            "EBIT":          round(ebit),
            "PAT":           round(pat_new),
            "FCF":           round(fcf),
            "Capex":         round(capex_new),
            "Net Debt":      round(net_debt),
            "EPS (₹)":      round(eps, 1),
        })

        prev = {
            "revenue": rev, "ebitda": ebitda_new, "pat": pat_new,
            "depreciation": dep, "capex": capex_new,
            "total_debt": prev["total_debt"] * 0.95,
            "cash": prev["cash"] + fcf * 0.3,
            "equity": equity_new,
        }

    return pd.DataFrame(rows).set_index("Year")

def calculate_ratios(ticker, proj_df):
    info = get_company_info(ticker)
    ratios = {}
    for yr in proj_df.index:
        rev    = proj_df.loc[yr, "Revenue"]
        ebitda = proj_df.loc[yr, "EBITDA"]
        pat    = proj_df.loc[yr, "PAT"]
        fcf    = proj_df.loc[yr, "FCF"]
        nd     = proj_df.loc[yr, "Net Debt"]
        ratios[yr] = {
            "EBITDA Margin (%)": proj_df.loc[yr, "EBITDA Margin"],
            "PAT Margin (%)":    round(pat / rev * 100, 1),
            "FCF Margin (%)":    round(fcf / rev * 100, 1),
            "FCF/EBITDA (%)":    round(fcf / ebitda * 100, 1),
            "Net Debt/EBITDA":   round(nd / ebitda, 1) if ebitda else 0,
            "EPS (₹)":          proj_df.loc[yr, "EPS (₹)"],
        }
    return pd.DataFrame(ratios).T

def print_model(ticker):
    console = Console()
    console.print(f"\n[bold cyan]━━━ Financial Projections ━━━[/bold cyan]")
    proj   = project_financials(ticker)
    ratios = calculate_ratios(ticker, proj)

    t = Table(show_header=True, header_style="bold magenta")
    t.add_column("Metric (₹ crore)", style="cyan", width=22)
    for yr in proj.index:
        t.add_column(yr, justify="right", width=12)
    for metric in proj.columns:
        fmt = proj[metric]
        t.add_row(metric, *[
            f"{proj.loc[yr, metric]:,.1f}"
            if isinstance(proj.loc[yr, metric], float)
            else f"{proj.loc[yr, metric]:,}"
            for yr in proj.index
        ])
    console.print(t)

    console.print(f"\n[bold cyan]━━━ Key Ratios ━━━[/bold cyan]")
    t2 = Table(show_header=True, header_style="bold magenta")
    t2.add_column("Ratio", style="cyan", width=22)
    for yr in ratios.index:
        t2.add_column(yr, justify="right", width=12)
    for metric in ratios.columns:
        t2.add_row(metric, *[str(ratios.loc[yr, metric]) for yr in ratios.index])
    console.print(t2)

if __name__ == "__main__":
    print_model("RELIANCE.NS")