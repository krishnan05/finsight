from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import financials, valuation, scenarios, sentiment

app = FastAPI(
    title="ICICI Bank Equity Research API",
    description="Financial modelling engine — Phases 2 & 3",
    version="1.0.0"
)

# Allow React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(financials.router, prefix="/api")
app.include_router(valuation.router,  prefix="/api")
app.include_router(scenarios.router,  prefix="/api")
app.include_router(sentiment.router,  prefix="/api")

@app.get("/")
def root():
    return {"status": "ICICI Research Engine running"}