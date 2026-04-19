import pandas as pd
from rich.console import Console
from rich.table import Table
from rich import box

# ── Three scenario assumption sets ──────────────────────────────────────────

SCENARIOS = {
    "🐻 Bear": {
        "loan_growth":    [0.12, 0.10, 0.09],
        "nim":            [0.043, 0.041, 0.040],
        "cost_to_income": [0.400, 0.395, 0.390],
        "credit_cost":    [0.010, 0.012, 0.013],  # NPAs rise
        "non_ii_growth":  0.07,
        "tax_rate":       0.25,
        "retention":      0.70,
        "description":    "Rate cuts compress NIM, credit cycle turns, slow growth",
    },
    "📊 Base": {
        "loan_growth":    [0.16, 0.15, 0.14],
        "nim":            [0.046, 0.045, 0.044],
        "cost_to_income": [0.375, 0.370, 0.365],
        "credit_cost":    [0.007, 0.007, 0.008],
        "non_ii_growth":  0.10,
        "tax_rate":       0.25,
        "retention":      0.70,
        "description":    "Steady growth, mild NIM compression, stable asset quality",
    },
    "🐂 Bull": {
        "loan_growth":    [0.20, 0.18, 0.17],
        "nim":            [0.048, 0.047, 0.047],  # NIM holds up
        "cost_to_income": [0.360, 0.355, 0.350],  # operating leverage kicks in
        "credit_cost":    [0.005, 0.005, 0.006],  # asset quality stays pristine
        "non_ii_growth":  0.14,
        "tax_rate":       0.25,
        "retention":      0.70,
        "description":    "Strong credit demand, NIM holds, operating leverage, clean book",
    },
}

HISTORICAL_FY2024 = {
    "advances": 1_261_491,
    "deposits": 1_412_825,
    "equity":   218_177,
    "non_ii":   22_958,
    "pat":      40_888,
}

PROJ_YEARS = ["FY2025E", "FY2026E", "FY2027E"]
SHARES     = 703  # crore

# ── Valuation multiples per scenario ────────────────────────────────────────
MULTIPLES = {
    "🐻 Bear": {"pe": 14.0, "pbv": 2.2},
    "📊 Base": {"pe": 18.0, "pbv": 2.76},
    "🐂 Bull": {"pe": 22.0, "pbv": 3.3},
}


def run_scenario(name, ass):
    rows = []
    prev = HISTORICAL_FY2024.copy()

    for i, yr in enumerate(PROJ_YEARS):
        adv      = prev["advances"] * (1 + ass["loan_growth"][i])
        dep      = prev["deposits"] * (1 + ass["loan_growth"][i])
        nii      = adv * ass["nim"][i]
        non_ii   = prev["non_ii"] * (1 + ass["non_ii_growth"])
        tot      = nii + non_ii
        opex     = tot * ass["cost_to_income"][i]
        ppop     = tot - opex
        prov     = adv * ass["credit_cost"][i]
        pbt      = ppop - prov
        pat      = pbt * (1 - ass["tax_rate"])
        equity   = prev["equity"] + pat * ass["retention"]

        rows.append({
            "Year":       yr,
            "Advances":   round(adv),
            "NII":        round(nii),
            "Total Inc":  round(tot),
            "PPOP":       round(ppop),
            "Provisions": round(prov),
            "PAT":        round(pat),
            "Equity":     round(equity),
            "EPS (₹)":   round(pat / SHARES, 1),
            "BV/Shr (₹)":round(equity / SHARES, 1),
            "ROE (%)":    round(pat / equity * 100, 1),
            "NIM (%)":    round(ass["nim"][i] * 100, 2),
        })
        prev = {
            "advances": adv, "deposits": dep,
            "equity": equity, "non_ii": non_ii, "pat": pat,
        }

    return pd.DataFrame(rows).set_index("Year")


def price_targets():
    targets = {}
    for name, ass in SCENARIOS.items():
        df   = run_scenario(name, ass)
        mult = MULTIPLES[name]

        pat_fy27  = df.loc["FY2027E", "PAT"]
        bv_fy27   = df.loc["FY2027E", "Equity"]
        eps_fy27  = df.loc["FY2027E", "EPS (₹)"]
        bvps_fy27 = df.loc["FY2027E", "BV/Shr (₹)"]

        pe_target  = round(eps_fy27  * mult["pe"],  0)
        pbv_target = round(bvps_fy27 * mult["pbv"], 0)
        avg_target = round((pe_target + pbv_target) / 2, 0)

        # upside/downside vs current price
        current = 1346.8
        upside  = round((avg_target - current) / current * 100, 1)

        targets[name] = {
            "EPS FY27E (₹)":   eps_fy27,
            "P/E Multiple":     mult["pe"],
            "P/E Target (₹)":  pe_target,
            "BV/Shr FY27E (₹)":bvps_fy27,
            "P/BV Multiple":    mult["pbv"],
            "P/BV Target (₹)": pbv_target,
            "Avg Target (₹)":  avg_target,
            "Upside/Down (%)": upside,
        }
    return pd.DataFrame(targets).T


def print_scenarios():
    console = Console()

    for name, ass in SCENARIOS.items():
        df = run_scenario(name, ass)
        console.print(f"\n[bold yellow]{name}[/bold yellow] — {ass['description']}")

        t = Table(show_header=True, header_style="bold white",
                  box=box.SIMPLE_HEAVY)
        t.add_column("Metric", style="cyan", width=14)
        for yr in df.index:
            t.add_column(yr, justify="right", width=12)

        key_metrics = ["NII", "PAT", "EPS (₹)", "BV/Shr (₹)", "ROE (%)", "NIM (%)"]
        for m in key_metrics:
            vals = []
            for yr in df.index:
                v = df.loc[yr, m]
                vals.append(f"{v:,.1f}" if isinstance(v, float) else f"{v:,}")
            t.add_row(m, *vals)
        console.print(t)

    # Price target summary
    console.print("\n[bold cyan]━━━ PRICE TARGET SUMMARY ━━━[/bold cyan]")
    console.print(f"[dim]Current Price: ₹1,346.8[/dim]\n")

    pt = price_targets()
    t2 = Table(show_header=True, header_style="bold magenta", box=box.HEAVY_EDGE)
    t2.add_column("Scenario",       style="bold", width=12)
    t2.add_column("P/E Target",     justify="right", width=12)
    t2.add_column("P/BV Target",    justify="right", width=12)
    t2.add_column("Avg Target (₹)", justify="right", width=14)
    t2.add_column("Upside (%)",     justify="right", width=12)

    colors = {"🐻 Bear": "red", "📊 Base": "yellow", "🐂 Bull": "green"}
    for scenario in pt.index:
        row = pt.loc[scenario]
        color = colors.get(scenario, "white")
        upside_str = f"[{color}]{row['Upside/Down (%)']:+.1f}%[/{color}]"
        t2.add_row(
            scenario,
            f"₹{row['P/E Target (₹)']:,.0f}",
            f"₹{row['P/BV Target (₹)']:,.0f}",
            f"[bold {color}]₹{row['Avg Target (₹)']:,.0f}[/bold {color}]",
            upside_str,
        )
    console.print(t2)


if __name__ == "__main__":
    print_scenarios()