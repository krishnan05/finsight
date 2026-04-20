import pandas as pd
from rich.console import Console
from rich.table import Table
from rich import box
from src.data.fetch import get_company_info
from src.financial.templates import get_template

PROJ_YEARS = ["FY2025E", "FY2026E", "FY2027E"]

SCENARIO_MULTIPLIERS = {
    "🐻 Bear": {
        "revenue_growth_adj":  -0.04,
        "ebitda_margin_adj":   -0.02,
        "capex_adj":           +0.02,
        "ev_ebitda_adj":       -0.20,
        "pe_adj":              -0.20,
        "description": "Demand slowdown, margin compression, multiple contraction",
    },
    "📊 Base": {
        "revenue_growth_adj":   0.00,
        "ebitda_margin_adj":    0.00,
        "capex_adj":            0.00,
        "ev_ebitda_adj":        0.00,
        "pe_adj":               0.00,
        "description": "Steady growth, margins in line with sector template",
    },
    "🐂 Bull": {
        "revenue_growth_adj":  +0.04,
        "ebitda_margin_adj":   +0.02,
        "capex_adj":           -0.01,
        "ev_ebitda_adj":       +0.20,
        "pe_adj":              +0.20,
        "description": "Strong demand, operating leverage, multiple expansion",
    },
}

def run_scenario(ticker, scenario_name):
    from src.financial.model import get_base_financials
    info  = get_company_info(ticker)
    base  = get_base_financials(ticker)
    tmpl  = get_template(info["sector"])
    adj   = SCENARIO_MULTIPLIERS[scenario_name]

    revenue  = base["revenue"]     or 100000
    ebitda   = base["ebitda"]      or revenue * tmpl["ebitda_margin"][0]
    pat      = base["pat"]         or revenue * 0.08
    net_debt = (base["total_debt"] or 0) - (base["cash"] or 0)
    shares   = info.get("shares_cr") or 100
    equity   = base["equity"]      or revenue * 0.5

    rows = []
    prev = {"revenue": revenue, "ebitda": ebitda, "pat": pat,
            "net_debt": net_debt, "equity": equity}

    for i, yr in enumerate(PROJ_YEARS):
        growth    = tmpl["revenue_growth"][i] + adj["revenue_growth_adj"]
        margin    = tmpl["ebitda_margin"][i]  + adj["ebitda_margin_adj"]
        capex_pct = tmpl["capex_pct_rev"]     + adj["capex_adj"]

        rev        = prev["revenue"] * (1 + growth)
        ebitda_new = rev * margin
        dep        = rev * 0.04
        ebit       = ebitda_new - dep
        capex_new  = rev * capex_pct
        wc_change  = rev * tmpl["wc_pct_rev"] * 0.1
        tax        = ebit * tmpl["tax_rate"]
        pat_new    = max(ebit - tax - prev["net_debt"] * 0.07, 0)
        fcf        = ebitda_new - tax - capex_new - wc_change
        equity_new = prev["equity"] + pat_new * 0.70
        eps        = pat_new / shares if shares else 0

        rows.append({
            "Year":     yr,
            "Revenue":  round(rev),
            "EBITDA":   round(ebitda_new),
            "PAT":      round(pat_new),
            "FCF":      round(fcf),
            "EPS (₹)": round(eps, 1),
            "EBITDA %": round(margin * 100, 1),
        })
        prev = {"revenue": rev, "ebitda": ebitda_new, "pat": pat_new,
                "net_debt": prev["net_debt"] * 0.95, "equity": equity_new}

    return pd.DataFrame(rows).set_index("Year")

def get_price_targets(ticker):
    info    = get_company_info(ticker)
    tmpl    = get_template(info["sector"])
    current = info.get("current_price") or 1000
    shares  = info.get("shares_cr") or 100
    net_debt= info.get("net_debt_cr") or 0
    targets = {}

    for name, adj in SCENARIO_MULTIPLIERS.items():
        df = run_scenario(ticker, name)
        ebitda_27 = df.loc["FY2027E", "EBITDA"]
        pat_27    = df.loc["FY2027E", "PAT"]
        eps_27    = df.loc["FY2027E", "EPS (₹)"]

        ev_range  = tmpl["ev_ebitda_range"] or (10, 18)
        pe_range  = tmpl["pe_range"]
        base_ev_mult = (ev_range[0] + ev_range[1]) / 2
        base_pe_mult = (pe_range[0] + pe_range[1]) / 2

        ev_mult = base_ev_mult * (1 + adj["ev_ebitda_adj"])
        pe_mult = base_pe_mult * (1 + adj["pe_adj"])

        ev_target    = ebitda_27 * ev_mult
        equity_val   = ev_target - net_debt
        ev_price     = round(equity_val / shares) if shares else 0
        pe_price     = round(eps_27 * pe_mult)
        avg_target   = round((ev_price + pe_price) / 2)
        upside       = round((avg_target - current) / current * 100, 1)

        targets[name] = {
            "EV/EBITDA Target (₹)": ev_price,
            "P/E Target (₹)":       pe_price,
            "Avg Target (₹)":       avg_target,
            "Upside (%)":           upside,
            "Description":          adj["description"],
        }
    return pd.DataFrame(targets).T

def print_scenarios(ticker):
    console = Console()
    info    = get_company_info(ticker)

    for name in SCENARIO_MULTIPLIERS:
        adj = SCENARIO_MULTIPLIERS[name]
        df  = run_scenario(ticker, name)
        console.print(f"\n[bold yellow]{name}[/bold yellow] — {adj['description']}")
        t = Table(show_header=True, header_style="bold white",
                  box=box.SIMPLE_HEAVY)
        t.add_column("Metric", style="cyan", width=14)
        for yr in df.index:
            t.add_column(yr, justify="right", width=12)
        for metric in ["Revenue", "EBITDA", "PAT", "FCF", "EPS (₹)", "EBITDA %"]:
            t.add_row(metric, *[
                f"{df.loc[yr, metric]:,.1f}"
                if isinstance(df.loc[yr, metric], float)
                else f"{df.loc[yr, metric]:,}"
                for yr in df.index
            ])
        console.print(t)

    console.print(f"\n[bold cyan]━━━ Price Target Summary ━━━[/bold cyan]")
    console.print(f"[dim]Current Price: ₹{info.get('current_price')}[/dim]\n")
    targets = get_price_targets(ticker)
    t2 = Table(show_header=True, header_style="bold magenta", box=box.HEAVY_EDGE)
    t2.add_column("Scenario",    style="bold", width=14)
    t2.add_column("EV/EBITDA",   justify="right", width=14)
    t2.add_column("P/E Target",  justify="right", width=12)
    t2.add_column("Avg Target",  justify="right", width=12)
    t2.add_column("Upside (%)",  justify="right", width=12)
    colors = {"🐻 Bear": "red", "📊 Base": "yellow", "🐂 Bull": "green"}
    for scenario in targets.index:
        row   = targets.loc[scenario]
        color = colors.get(scenario, "white")
        t2.add_row(
            scenario,
            f"₹{row['EV/EBITDA Target (₹)']:,}",
            f"₹{row['P/E Target (₹)']:,}",
            f"[bold {color}]₹{row['Avg Target (₹)']:,}[/bold {color}]",
            f"[{color}]{row['Upside (%)']:+.1f}%[/{color}]",
        )
    console.print(t2)

if __name__ == "__main__":
    print_scenarios("RELIANCE.NS")