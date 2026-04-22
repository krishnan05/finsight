# FinSight — AI-Powered Equity Research Platform

End-to-end equity research platform for any NSE-listed company.

## Live Demo
- **Web App**: https://finsight.vercel.app
- **API Docs**: https://finsight-api.onrender.com/docs

## What It Does
- Fetches live financial data for any NSE ticker via yfinance
- Projects 3-year Income Statement (Revenue, EBITDA, PAT, FCF)
- Bull / Base / Bear scenario analysis with price targets
- DCF + EV/EBITDA + P/E valuation with CAPM cost of equity
- LSTM time-series forecasting (PyTorch, Monte Carlo Dropout CI)
- FinBERT sentiment analysis on live news headlines
- Ensemble signal combining all three — BUY/HOLD/SELL rating
- Auto-generates professional PDF research report
- React dashboard with interactive scenario explorer

## Tech Stack
- **Backend**: Python, FastAPI, pandas, yfinance
- **ML**: PyTorch LSTM, HuggingFace FinBERT, scikit-learn
- **Frontend**: React, Recharts, Axios
- **Deploy**: Vercel (frontend) + Render (backend)

## Run Locally
```bash
# Backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm start

# CLI
python3 main.py RELIANCE.NS
python3 main.py INFY.NS
```

## Project Phases
- Phase 1: Excel 3-statement + DCF model (ICICI Bank)
- Phase 2: Python financial engine — fetch, model, scenarios, valuation
- Phase 3: ML layer — LSTM forecasting + FinBERT NLP + Ensemble signal
- Phase 4: React web app + FastAPI backend + PDF report generator

## Data Sources
ICICI Bank / NSE Annual Reports · yfinance · ProsusAI/FinBERT
