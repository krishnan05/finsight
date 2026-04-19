import pandas as pd
import numpy as np
from src.fetch import get_income_statement, get_balance_sheet, get_current_price

# ── Historical data from Annual Reports (Phase 1 verified) ──────────────────
HISTORICAL = {
    "FY2022": {"nii": 42777, "non_ii": 16213, "opex": 21785,
               "provisions": 9985,  "pat": 23339,
               "advances": 907927,  "deposits": 961674, "equity": 155025},
    "FY2023": {"nii": 54180, "non_ii": 19831, "opex": 26804,
               "provisions": 17190, "pat": 31896,
               "advances": 1079744, "deposits": 1136855, "equity": 180486},
    "FY2024": {"nii": 71445, "non_ii": 22958, "opex": 32873,
               "provisions": 17242, "pat": 40888,
               "advances": 1261491, "deposits": 1412825, "equity": 218177},
}

# ── Projection assumptions (Base Case) ──────────────────────────────────────
ASSUMPTIONS = {
    "loan_growth":    [0.16, 0.15, 0.14],   # FY25E, FY26E, FY27E
    "deposit_growth": [0.17, 0.15, 0.14],
    "nim":            [0.046, 0.045, 0.044],
    "cost_to_income": [0.375, 0.370, 0.365],
    "credit_cost":    [0.007, 0.007, 0.008],
    "tax_rate":       0.25,
    "proj_years":     ["FY2025E", "FY2026E", "FY2027E"],
}

def project_income_statement():
    rows = []
    prev = HISTORICAL["FY2024"].copy()

    for i, yr in enumerate(ASSUMPTIONS["proj_years"]):
        adv  = prev["advances"]  * (1 + ASSUMPTIONS["loan_growth"][i])
        dep  = prev["deposits"]  * (1 + ASSUMPTIONS["deposit_growth"][i])
        nii  = adv * ASSUMPTIONS["nim"][i]
        # non-interest income grows at 10% conservatively
        non_ii = prev["non_ii"] * 1.10
        total_income = nii + non_ii
        opex = total_income * ASSUMPTIONS["cost_to_income"][i]
        ppop = total_income - opex
        provisions = adv * ASSUMPTIONS["credit_cost"][i]
        pbt  = ppop - provisions
        pat  = pbt * (1 - ASSUMPTIONS["tax_rate"])
        equity = prev["equity"] + pat * 0.70
        rows.append({
            "Year":         yr,
            "Net Advances": round(adv),
            "Deposits":     round(dep),
            "NII":          round(nii),
            "Non-II":       round(non_ii),
            "Total Income": round(total_income),
            "Opex":         round(opex),
            "PPOP":         round(ppop),
            "Provisions":   round(provisions),
            "PBT":          round(pbt),
            "PAT":          round(pat),
            "Equity":       round(equity),
        })
        prev = {"advances": adv, "deposits": dep, "equity": equity,
                "non_ii": non_ii, "pat": pat}

    return pd.DataFrame(rows).set_index("Year")

def calculate_ratios(proj_df):
    ratios = {}
    shares = 703  # crore shares outstanding

    for yr in proj_df.index:
        pat    = proj_df.loc[yr, "PAT"]
        equity = proj_df.loc[yr, "Equity"]
        adv    = proj_df.loc[yr, "Net Advances"]
        nii    = proj_df.loc[yr, "NII"]
        opex   = proj_df.loc[yr, "Opex"]
        total  = proj_df.loc[yr, "Total Income"]

        ratios[yr] = {
            "ROE (%)":           round(pat / equity * 100, 1),
            "ROA (%)":           round(pat / adv * 100, 1),  # simplified
            "NIM (%)":           round(nii / adv * 100, 1),
            "Cost-to-Income (%)":round(opex / total * 100, 1),
            "EPS (₹)":          round(pat / shares, 2),
            "BV/Share (₹)":     round(equity / shares, 2),
        }
    return pd.DataFrame(ratios).T

def print_model():
    from rich.console import Console
    from rich.table import Table

    console = Console()
    proj = project_income_statement()
    ratios = calculate_ratios(proj)

    console.print("\n[bold cyan]━━━ ICICI Bank – Projected Income Statement (₹ crore) ━━━[/bold cyan]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", width=18)
    for yr in proj.index:
        table.add_column(yr, justify="right")
    for metric in proj.columns:
        table.add_row(metric, *[f"{proj.loc[yr, metric]:,.0f}" for yr in proj.index])
    console.print(table)

    console.print("\n[bold cyan]━━━ Key Ratios ━━━[/bold cyan]")
    table2 = Table(show_header=True, header_style="bold magenta")
    table2.add_column("Ratio", style="cyan", width=22)
    for yr in ratios.index:
        table2.add_column(yr, justify="right")
    for metric in ratios.columns:
        table2.add_row(metric, *[str(ratios.loc[yr, metric]) for yr in ratios.index])
    console.print(table2)

if __name__ == "__main__":
    print_model()