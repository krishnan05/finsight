from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import financials, valuation, scenarios, sentiment, ml

app = FastAPI(
    title="FinSight Equity Research API",
    description="General company financial modelling engine",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://finsight-kappa-neon.vercel.app/",  # replace with your actual Vercel URL
        "*"  # remove this in production if you want to be strict
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(financials.router, prefix="/api")
app.include_router(valuation.router, prefix="/api")
app.include_router(scenarios.router, prefix="/api")
app.include_router(sentiment.router, prefix="/api")
app.include_router(ml.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "FinSight Research Engine running", "version": "2.0.0"}