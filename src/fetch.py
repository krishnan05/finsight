import yfinance as yf
import pandas as pd
from rich import print as rprint

TICKER = "ICICIBANK.NS"

def get_ticker():
    return yf.Ticker(TICKER)

def get_income_statement(annual=True):
    t = get_ticker()
    df = t.financials if annual else t.quarterly_financials
    # yfinance returns columns as dates — convert to fiscal year labels
    df.columns = [f"FY{col.year}" if col.month <= 6 else f"FY{col.year+1}"
                  for col in df.columns]
    return df

def get_balance_sheet(annual=True):
    t = get_ticker()
    df = t.balance_sheet if annual else t.quarterly_balance_sheet
    df.columns = [f"FY{col.year}" if col.month <= 6 else f"FY{col.year+1}"
                  for col in df.columns]
    return df

def get_current_price():
    t = get_ticker()
    info = t.info
    return {
        "current_price":     info.get("currentPrice"),
        "market_cap_cr":     round(info.get("marketCap", 0) / 1e7, 0),  # convert to crore
        "pe_ratio":          info.get("trailingPE"),
        "pb_ratio":          info.get("priceToBook"),
        "52w_high":          info.get("fiftyTwoWeekHigh"),
        "52w_low":           info.get("fiftyTwoWeekLow"),
        "book_value":        info.get("bookValue"),
        "eps_ttm":           info.get("trailingEps"),
        "dividend_yield":    info.get("dividendYield"),
        "roe":               info.get("returnOnEquity"),
    }

def get_price_history(period="5y"):
    t = get_ticker()
    return t.history(period=period)

def print_summary():
    rprint("\n[bold blue]━━━ ICICI Bank Live Data ━━━[/bold blue]")
    data = get_current_price()
    for k, v in data.items():
        rprint(f"  [green]{k:<20}[/green] {v}")

if __name__ == "__main__":
    print_summary()