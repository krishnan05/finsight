import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime



# ── Sector / company keywords for relevance filtering ───────────────────────
RELEVANT_KEYWORDS = [
     "bank", "npa", "loan", "credit", "rbi", "rate",
    "profit", "earnings", "deposit", "nim", "casa", "dividend",
    "quarter", "results", "growth", "interest", "asset"
]

def fetch_news(ticker, max_articles=20):
    t = yf.Ticker(ticker)
    news = t.news
    if not news:
        return []
    articles = []
    for item in news[:max_articles]:
        # handle both old and new yfinance news format
        content = item.get("content", {})
        title   = (content.get("title") or
                   item.get("title") or "")
        summary = (content.get("summary") or
                   item.get("summary") or "")
        pub_date = (content.get("pubDate") or
                    item.get("providerPublishTime") or "")
        if title:
            articles.append({
                "title":   title,
                "summary": summary[:200] if summary else "",
                "date":    pub_date,
            })
    return articles


def is_relevant(text):
    text_lower = text.lower()
    return any(kw in text_lower for kw in RELEVANT_KEYWORDS)


def score_sentiment(articles):
    analyzer = SentimentIntensityAnalyzer()
    scored = []
    for a in articles:
        text = a["title"] + " " + a["summary"]
        if not is_relevant(text):
            continue
        scores  = analyzer.polarity_scores(text)
        compound = scores["compound"]  # -1 (very negative) to +1 (very positive)
        label = (
            "🟢 Positive" if compound >= 0.05 else
            "🔴 Negative" if compound <= -0.05 else
            "⚪ Neutral"
        )
        scored.append({
            "title":    a["title"][:75] + "..." if len(a["title"]) > 75
                        else a["title"],
            "score":    round(compound, 3),
            "label":    label,
            "date":     a["date"],
        })
    return scored


def aggregate_sentiment(scored):
    if not scored:
        return None
    scores   = [s["score"] for s in scored]
    avg      = round(sum(scores) / len(scores), 3)
    positive = sum(1 for s in scores if s >= 0.05)
    negative = sum(1 for s in scores if s <= -0.05)
    neutral  = len(scores) - positive - negative
    signal   = (
        "🐂 BULLISH  — Lean toward Bull case"  if avg >= 0.10 else
        "🐻 BEARISH  — Lean toward Bear case"  if avg <= -0.05 else
        "📊 NEUTRAL  — Stick with Base case"
    )
    return {
        "avg_score":  avg,
        "positive":   positive,
        "negative":   negative,
        "neutral":    neutral,
        "total":      len(scored),
        "signal":     signal,
    }


def scenario_adjustment(avg_score):
    """
    Translate sentiment score into a price target adjustment.
    Strong positive sentiment → add small premium to base target.
    Strong negative → apply discount.
    """
    if avg_score >= 0.15:
        return +0.05, "Strong positive news flow → +5% premium on base target"
    elif avg_score >= 0.05:
        return +0.02, "Mild positive news flow → +2% premium on base target"
    elif avg_score <= -0.10:
        return -0.05, "Strong negative news flow → -5% discount on base target"
    elif avg_score <= -0.05:
        return -0.02, "Mild negative news flow → -2% discount on base target"
    else:
        return 0.00, "Neutral news flow → no adjustment to base target"


def print_sentiment(ticker):
    from src.financial.scenarios import get_price_targets

    console = Console()
    console.print("\n[bold blue]━━━ Phase 3: Sentiment Analysis ━━━[/bold blue]")
    console.print(f"[dim]Fetching recent news for {ticker}...[/dim]\n")

    articles = fetch_news(ticker)
    if not articles:
        console.print("[red]No news found. Check ticker or internet connection.[/red]")
        return

    scored = score_sentiment(articles)
    if not scored:
        console.print("[yellow]News fetched but no relevant articles found.[/yellow]")
        return

    # Article table
    t = Table(show_header=True, header_style="bold magenta",
              box=box.SIMPLE_HEAVY, show_lines=False)
    t.add_column("Headline",  width=60)
    t.add_column("Sentiment", width=14, justify="center")
    t.add_column("Score",     width=8,  justify="right")

    for s in scored:
        color = ("green" if "Positive" in s["label"] else
                 "red"   if "Negative" in s["label"] else "white")
        t.add_row(
            f"[{color}]{s['title']}[/{color}]",
            s["label"],
            f"{s['score']:+.3f}",
        )
    console.print(t)

    # Aggregate
    agg      = aggregate_sentiment(scored)
    adj, adj_note = scenario_adjustment(agg["avg_score"])

    console.print("\n[bold cyan]━━━ Sentiment Summary ━━━[/bold cyan]")
    console.print(f"  Articles analysed : {agg['total']}")
    console.print(f"  🟢 Positive       : {agg['positive']}")
    console.print(f"  🔴 Negative       : {agg['negative']}")
    console.print(f"  ⚪ Neutral        : {agg['neutral']}")
    console.print(f"  Avg Score         : {agg['avg_score']:+.3f}  "
                  f"(range: -1.0 to +1.0)")
    console.print(f"\n  Signal  → [bold]{agg['signal']}[/bold]")

    # Get actual base target for this company
    try:
        targets     = get_price_targets(ticker)
        base_target = int(targets.loc["📊 Base", "Avg Target (₹)"])
    except Exception:
        base_target = 1000  # neutral fallback if valuation fails

    adjusted = round(base_target * (1 + adj))

    console.print(f"\n[bold cyan]━━━ Sentiment-Adjusted Price Target ━━━[/bold cyan]")
    console.print(f"  Base model target    : ₹{base_target:,}")
    console.print(f"  Sentiment adjustment : {adj*100:+.0f}%  ({adj_note})")
    console.print(f"  Adjusted target      : [bold green]₹{adjusted:,}[/bold green]")
    console.print(f"\n  [dim]Note: Sentiment is a qualitative overlay, "
                  f"not a replacement for fundamental analysis.[/dim]\n")
    
if __name__ == "__main__":
    print_sentiment()