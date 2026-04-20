import sys
from rich.console import Console

console = Console()

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "RELIANCE.NS"
    if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
        ticker += ".NS"

    console.print(f"\n[bold white on blue]  FINSIGHT – EQUITY RESEARCH ENGINE  [/bold white on blue]")
    console.print(f"[dim]Analysing: {ticker}[/dim]\n")

    from src.data.fetch          import print_summary
    from src.financial.model     import print_model
    from src.financial.scenarios import print_scenarios
    from src.financial.valuation import run_full_valuation, print_valuation
    from src.ml.lstm             import print_ml_forecast, run_lstm_forecast
    from src.ml.finbert          import print_sentiment, score_sentiment, \
                                        fetch_news, aggregate_sentiment
    from src.ml.ensemble         import print_ensemble

    # Run all modules
    print_summary(ticker)
    print_model(ticker)
    print_scenarios(ticker)
    print_valuation(ticker)

    # Capture outputs for ensemble
    val_results  = run_full_valuation(ticker)
    lstm_mean, _, _, _ = run_lstm_forecast(ticker)
    print_ml_forecast(ticker)

    articles     = fetch_news(ticker)
    scored       = score_sentiment(articles)
    sent_agg     = aggregate_sentiment(scored)
    print_sentiment(ticker)

    # Ensemble — combines all three signals
    print_ensemble(ticker, val_results, lstm_mean, sent_agg)

    console.print(f"[bold green]✓ Analysis complete: {ticker}[/bold green]\n")