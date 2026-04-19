from fastapi import APIRouter
from src.fetch import get_current_price
from src.model import project_income_statement, calculate_ratios

router = APIRouter()

@router.get("/financials")
def get_financials():
    live    = get_current_price()
    proj    = project_income_statement()
    ratios  = calculate_ratios(proj)

    return {
        "live": live,
        "projections": proj.reset_index().to_dict(orient="records"),
        "ratios":      ratios.reset_index().to_dict(orient="records"),
    }