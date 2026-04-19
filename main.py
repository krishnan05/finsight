import sys
from rich.console import Console
from src.data.fetch import print_summary
from src.financial.model  import print_model
from src.financial.scenarios import print_scenarios
from src.financial.valuation import print_valuation
from src.ml.lstm import print_ml_forecast
from src.ml.finbert import print_sentiment
console = Console()

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "RELIANCE.NS"
    if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
        ticker += ".NS"

    console.print(f"\n[bold white on blue]  FINSIGHT – EQUITY RESEARCH ENGINE  [/bold white on blue]")
    console.print(f"[dim]Analysing: {ticker}[/dim]\n")


    print_summary(ticker)
    print_model(ticker)
    print_scenarios(ticker)
    print_valuation(ticker)
    print_ml_forecast(ticker)
    print_sentiment(ticker)

    console.print(f"\n[bold green]✓ Analysis complete: {ticker}[/bold green]\n")