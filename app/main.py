from fastapi import FastAPI

from app.routes.companies import router as companies_router
from app.routes.financials import router as financials_router
from app.routes.analytics import router as analytics_router
from app.routes.valuation import router as valuation_router
from app.routes.summary import router as summary_router


app = FastAPI(
    title="Nifty 100 Analytics API",
    version="1.0.0"
)


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


app.include_router(companies_router)
app.include_router(financials_router)
app.include_router(analytics_router)
app.include_router(valuation_router)
app.include_router(summary_router)