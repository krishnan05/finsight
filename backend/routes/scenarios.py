from fastapi import APIRouter
from src.financial.scenarios import run_scenario, SCENARIOS, MULTIPLES, SHARES

router = APIRouter()

@router.get("/scenarios")
def get_scenarios():
    result = {}
    current_price = 1346.8

    for name, ass in SCENARIOS.items():
        df   = run_scenario(name, ass)
        mult = MULTIPLES[name]

        eps_fy27  = df.loc["FY2027E", "EPS (₹)"]
        bvps_fy27 = df.loc["FY2027E", "BV/Shr (₹)"]
        pat_fy27  = df.loc["FY2027E", "PAT"]

        pe_target  = round(eps_fy27  * mult["pe"],  0)
        pbv_target = round(bvps_fy27 * mult["pbv"], 0)
        avg_target = round((pe_target + pbv_target) / 2, 0)
        upside     = round((avg_target - current_price) / current_price * 100, 1)

        result[name] = {
            "projections": df.reset_index().to_dict(orient="records"),
            "pe_target":   pe_target,
            "pbv_target":  pbv_target,
            "avg_target":  avg_target,
            "upside":      upside,
            "description": ass["description"],
        }
    return result