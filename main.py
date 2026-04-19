from rich.console import Console
from src.fetch import get_income_statement, get_balance_sheet, get_current_price, print_summary
from src.model    import print_model
from src.scenarios import print_scenarios
from src.valuation import print_valuation

console = Console()

if __name__ == "__main__":
    console.print("\n[bold white on blue]  ICICI BANK – EQUITY RESEARCH ENGINE  [/bold white on blue]\n")
    print_summary()
    print_model()
    print_scenarios()
    print_valuation()
    console.print("\n[bold green]✓ Model complete.[/bold green]\n")