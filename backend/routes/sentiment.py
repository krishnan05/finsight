from fastapi import APIRouter
from src.ml.finbert import fetch_news, score_sentiment, aggregate_sentiment, scenario_adjustment

router = APIRouter()

@router.get("/sentiment")
def get_sentiment():
    articles = fetch_news()
    scored   = score_sentiment(articles)
    agg      = aggregate_sentiment(scored)

    if not agg:
        return {"error": "No relevant news found"}

    adj, note = scenario_adjustment(agg["avg_score"])

    return {
        "articles":     scored,
        "summary":      agg,
        "adjustment":   adj,
        "note":         note,
        "adjusted_target": round(940 * (1 + adj)),
    }