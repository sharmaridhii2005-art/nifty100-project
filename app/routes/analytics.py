from fastapi import APIRouter
import pandas as pd

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

CLUSTER_FILE = "output/cluster_labels.csv"
OUTLIER_FILE = "output/outlier_report.csv"
PORTFOLIO_FILE = "output/portfolio_stats.csv"


@router.get("/clusters")
def get_clusters():
    df = pd.read_csv(CLUSTER_FILE)

    return {
        "count": len(df),
        "unique_companies": df["company_id"].nunique(),
        "clusters": df.to_dict(orient="records")
    }


@router.get("/outliers")
def get_outliers():
    df = pd.read_csv(OUTLIER_FILE)

    return {
        "count": len(df),
        "outliers": df.to_dict(orient="records")
    }


@router.get("/portfolio-stats")
def get_portfolio_stats():
    df = pd.read_csv(PORTFOLIO_FILE)

    return {
        "count": len(df),
        "statistics": df.to_dict(orient="records")
    }