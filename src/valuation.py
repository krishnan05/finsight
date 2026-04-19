import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich import box
from src.scenarios import run_scenario, SCENARIOS, MULTIPLES, SHARES

CURRENT_PRICE = 1346.8
PROJ_YEARS    = ["FY2025E", "FY2026E", "FY2027E"]

# ── CAPM Cost of Equity ──────────────────────────────────────────────────────
def cost_of_equity(rf=0.069, erp=0.055, beta=1.2):
    """Ke = Rf + β × ERP"""
    return rf + beta * erp

# ── DDM Valuation ────────────────────────────────────────────────────────────
def ddm_valuation(pat_series, payout=0.20, ke=None, tgr=0.06):
    """
    3-stage DDM:
    - Near term dividends: 20% payout (growth phase)
    - Terminal value: uses 50% payout (mature phase)
    - Discount everything back at Ke
    """
    if ke is None:
        ke = cost_of_equity()

    # Near-term dividends at growth-phase payout
    dividends = [pat * payout for pat in pat_series]

    # PV of near-term dividends
    pv_divs = sum(d / (1 + ke)**t for t, d in enumerate(dividends, 1))

    # Terminal value uses mature payout of 50%
    terminal_dividend = pat_series[-1] * 0.50 * (1 + tgr)
    terminal_value    = terminal_dividend / (ke - tgr)
    pv_terminal       = terminal_value / (1 + ke)**len(dividends)

    equity_value    = pv_divs + pv_terminal   # ₹ crore
    price_per_share = equity_value / SHARES   # ₹ per share
    return round(price_per_share, 0)


# ── P/E Valuation ────────────────────────────────────────────────────────────
def pe_valuation(eps_fwd, multiple):
    return round(eps_fwd * multiple, 0)


# ── P/BV Valuation ───────────────────────────────────────────────────────────
def pbv_valuation(bvps_fwd, multiple):
    return round(bvps_fwd * multiple, 0)


# ── Full Valuation Engine ────────────────────────────────────────────────────
def run_full_valuation():
    ke  = cost_of_equity()
    results = {}

    for scenario, ass in SCENARIOS.items():
        df   = run_scenario(scenario, ass)
        mult = MULTIPLES[scenario]

        pat_series = [df.loc[yr, "PAT"]        for yr in PROJ_YEARS]
        eps_fy27   =  df.loc["FY2027E", "EPS (₹)"]
        bvps_fy27  =  df.loc["FY2027E", "BV/Shr (₹)"]

        # Adjust DDM terminal growth by scenario
        tgr_map = {"🐻 Bear": 0.05, "📊 Base": 0.06, "🐂 Bull": 0.07}
        tgr     = tgr_map[scenario]

        ddm  = ddm_valuation(pat_series, ke=ke, tgr=tgr)
        pe   = pe_valuation(eps_fy27,  mult["pe"])
        pbv  = pbv_valuation(bvps_fy27, mult["pbv"])

        # Weighted average: DDM 25%, P/E 37.5%, P/BV 37.5%
        # P/BV and P/E are primary for banks; DDM is a cross-check
        weighted = round(ddm * 0.25 + pe * 0.375 + pbv * 0.375, 0)
        upside   = round((weighted - CURRENT_PRICE) / CURRENT_PRICE * 100, 1)

        results[scenario] = {
            "DDM (₹)":          ddm,
            "P/E (₹)":          pe,
            "P/BV (₹)":         pbv,
            "Weighted Target":  weighted,
            "Upside (%)":       upside,
            "Rating":           _rating(upside),
        }

    return pd.DataFrame(results).T


def _rating(upside):
    if upside >= 15:  return "✅ BUY"
    if upside >= -5:  return "⚪ HOLD"
    return                    "🔴 SELL"


# ── CAPM Breakdown ───────────────────────────────────────────────────────────
def print_capm():
    console = Console()
    rf, erp, beta = 0.069, 0.055, 1.2
    ke = cost_of_equity(rf, erp, beta)
    console.print("\n[bold blue]━━━ CAPM – Cost of Equity ━━━[/bold blue]")
    console.print(f"  Risk-Free Rate (10Y G-Sec) : [cyan]{rf*100:.1f}%[/cyan]")
    console.print(f"  Equity Risk Premium        : [cyan]{erp*100:.1f}%[/cyan]")
    console.print(f"  Beta (ICICI Bank)          : [cyan]{beta}x[/cyan]")
    console.print(f"  ──────────────────────────────────────")
    console.print(f"  Cost of Equity (Ke)        : [bold green]{ke*100:.2f}%[/bold green]")
    console.print(f"  Formula: Ke = {rf*100}% + {beta} × {erp*100}% = {ke*100:.2f}%\n")


# ── Final Summary ────────────────────────────────────────────────────────────
def print_valuation():
    console = Console()
    print_capm()

    results = run_full_valuation()

    console.print("[bold cyan]━━━ ICICI Bank – Full Valuation Summary ━━━[/bold cyan]")
    console.print(f"[dim]Current Market Price: ₹{CURRENT_PRICE}  |  Method weights: DDM 25% · P/E 37.5% · P/BV 37.5%[/dim]\n")

    t = Table(show_header=True, header_style="bold magenta", box=box.HEAVY_EDGE)
    t.add_column("Scenario",         style="bold",   width=12)
    t.add_column("DDM (₹)",          justify="right", width=10)
    t.add_column("P/E (₹)",          justify="right", width=10)
    t.add_column("P/BV (₹)",         justify="right", width=10)
    t.add_column("Weighted (₹)",     justify="right", width=14)
    t.add_column("Upside (%)",        justify="right", width=12)
    t.add_column("Rating",            justify="center",width=10)

    colors = {"🐻 Bear": "red", "📊 Base": "yellow", "🐂 Bull": "green"}
    for scenario in results.index:
        row   = results.loc[scenario]
        color = colors.get(scenario, "white")
        upside_str = f"[{color}]{row['Upside (%)']:+.1f}%[/{color}]"
        t.add_row(
            scenario,
            f"₹{row['DDM (₹)']:,.0f}",
            f"₹{row['P/E (₹)']:,.0f}",
            f"₹{row['P/BV (₹)']:,.0f}",
            f"[bold {color}]₹{row['Weighted Target']:,.0f}[/bold {color}]",
            upside_str,
            row["Rating"],
        )
    console.print(t)

    # Investment thesis summary
    base = results.loc["📊 Base"]
    bull = results.loc["🐂 Bull"]
    bear = results.loc["🐻 Bear"]

    console.print("\n[bold white]━━━ Investment Thesis ━━━[/bold white]")
    console.print(f"  Base target  : [yellow]₹{base['Weighted Target']:,.0f}[/yellow]  ({base['Upside (%)']:+.1f}% upside)  →  {base['Rating']}")
    console.print(f"  Bull target  : [green]₹{bull['Weighted Target']:,.0f}[/green]  ({bull['Upside (%)']:+.1f}% upside)  →  {bull['Rating']}")
    console.print(f"  Bear target  : [red]₹{bear['Weighted Target']:,.0f}[/red]  ({bear['Upside (%)']:+.1f}% downside) →  {bear['Rating']}")
    console.print(f"\n  [dim]Key risks: NIM compression, CASA decline, credit cycle turn, RBI rate cuts[/dim]")
    console.print(f"  [dim]Key catalysts: Loan growth acceleration, fee income diversification, opex leverage[/dim]\n")


if __name__ == "__main__":
    print_valuation()