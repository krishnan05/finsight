import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich import box
from src.data.fetch import get_company_info
from src.financial.templates import get_template
from src.financial.scenarios import run_scenario, SCENARIO_MULTIPLIERS

PROJ_YEARS = ["FY2025E", "FY2026E", "FY2027E"]

def cost_of_equity(rf=0.069, erp=0.055, beta=1.1):
    return rf + beta * erp

def dcf_valuation(ticker, fcf_series, ke=None, wacc=None, tgr=0.055):
    info     = get_company_info(ticker)
    net_debt = info.get("net_debt_cr") or 0
    shares   = info.get("shares_cr")   or 100
    discount = wacc or ke or cost_of_equity()
    fcf_series = [max(f, 0) for f in fcf_series] 
    
    pv_fcfs = sum(f / (1 + discount)**t
                  for t, f in enumerate(fcf_series, 1))
    terminal_value = fcf_series[-1] * (1 + tgr) / (discount - tgr)
    pv_terminal    = terminal_value / (1 + discount)**len(fcf_series)
    enterprise_val = pv_fcfs + pv_terminal
    equity_val     = enterprise_val - net_debt
    price          = round(equity_val / shares) if shares else 0
    return price

def ev_ebitda_valuation(ticker, ebitda_fwd, multiple):
    info     = get_company_info(ticker)
    net_debt = info.get("net_debt_cr") or 0
    shares   = info.get("shares_cr")   or 100
    ev       = ebitda_fwd * multiple
    equity   = ev - net_debt
    return round(equity / shares) if shares else 0

def pe_valuation(eps_fwd, multiple):
    return round(eps_fwd * multiple)

def run_full_valuation(ticker):
    info    = get_company_info(ticker)
    tmpl    = get_template(info["sector"])
    current = info.get("current_price") or 1000
    ke      = cost_of_equity()
    results = {}

    tgr_map = {"🐻 Bear": 0.04, "📊 Base": 0.055, "🐂 Bull": 0.07}
    ev_mult_map = {
        "🐻 Bear": (tmpl["ev_ebitda_range"] or (10,18))[0] * 0.85,
        "📊 Base": sum(tmpl["ev_ebitda_range"] or (10,18)) / 2,
        "🐂 Bull": (tmpl["ev_ebitda_range"] or (10,18))[1] * 1.10,
    }
    pe_mult_map = {
        "🐻 Bear": tmpl["pe_range"][0] * 0.85,
        "📊 Base": sum(tmpl["pe_range"]) / 2,
        "🐂 Bull": tmpl["pe_range"][1] * 1.10,
    }

    for scenario in SCENARIO_MULTIPLIERS:
        df       = run_scenario(ticker, scenario)
        fcf_series = [df.loc[yr, "FCF"] for yr in PROJ_YEARS]
        ebitda_27  = df.loc["FY2027E", "EBITDA"]
        eps_27     = df.loc["FY2027E", "EPS (₹)"]

        dcf  = dcf_valuation(ticker, fcf_series, ke=ke, tgr=tgr_map[scenario])
        ev   = ev_ebitda_valuation(ticker, ebitda_27, ev_mult_map[scenario])
        pe   = pe_valuation(eps_27, pe_mult_map[scenario])

        weighted = round(dcf * 0.35 + ev * 0.40 + pe * 0.25)
        upside   = round((weighted - current) / current * 100, 1)

        results[scenario] = {
            "DCF (₹)":       dcf,
            "EV/EBITDA (₹)": ev,
            "P/E (₹)":       pe,
            "Weighted (₹)":  weighted,
            "Upside (%)":    upside,
            "Rating":        _rating(upside),
        }
    return pd.DataFrame(results).T

def _rating(upside):
    if upside >= 15:  return "✅ BUY"
    if upside >= -5:  return "⚪ HOLD"
    return                    "🔴 SELL"

def print_valuation(ticker):
    console = Console()
    info    = get_company_info(ticker)
    ke      = cost_of_equity()
    results = run_full_valuation(ticker)

    console.print(f"\n[bold blue]━━━ CAPM – Cost of Equity ━━━[/bold blue]")
    console.print(f"  Ke = 6.9% + 1.1 × 5.5% = [bold green]{ke*100:.2f}%[/bold green]")

    console.print(f"\n[bold cyan]━━━ Full Valuation Summary ━━━[/bold cyan]")
    console.print(f"[dim]CMP: ₹{info.get('current_price')} | "
                  f"Weights: DCF 35% · EV/EBITDA 40% · P/E 25%[/dim]\n")

    t = Table(show_header=True, header_style="bold magenta", box=box.HEAVY_EDGE)
    t.add_column("Scenario",      style="bold",   width=12)
    t.add_column("DCF (₹)",       justify="right", width=10)
    t.add_column("EV/EBITDA (₹)", justify="right", width=14)
    t.add_column("P/E (₹)",       justify="right", width=10)
    t.add_column("Weighted (₹)",  justify="right", width=14)
    t.add_column("Upside (%)",    justify="right", width=12)
    t.add_column("Rating",        justify="center",width=10)

    colors = {"🐻 Bear": "red", "📊 Base": "yellow", "🐂 Bull": "green"}
    for scenario in results.index:
        row   = results.loc[scenario]
        color = colors.get(scenario, "white")
        t.add_row(
            scenario,
            f"₹{row['DCF (₹)']:,}",
            f"₹{row['EV/EBITDA (₹)']:,}",
            f"₹{row['P/E (₹)']:,}",
            f"[bold {color}]₹{row['Weighted (₹)']:,}[/bold {color}]",
            f"[{color}]{row['Upside (%)']:+.1f}%[/{color}]",
            row["Rating"],
        )
    console.print(t)

    base = results.loc["📊 Base"]
    bull = results.loc["🐂 Bull"]
    bear = results.loc["🐻 Bear"]
    console.print(f"\n[bold white]━━━ Investment Thesis ━━━[/bold white]")
    console.print(f"  Base: [yellow]₹{base['Weighted (₹)']:,}[/yellow] "
                  f"({base['Upside (%)']:+.1f}%) → {base['Rating']}")
    console.print(f"  Bull: [green]₹{bull['Weighted (₹)']:,}[/green] "
                  f"({bull['Upside (%)']:+.1f}%) → {bull['Rating']}")
    console.print(f"  Bear: [red]₹{bear['Weighted (₹)']:,}[/red] "
                  f"({bear['Upside (%)']:+.1f}%) → {bear['Rating']}\n")

if __name__ == "__main__":
    print_valuation("RELIANCE.NS")