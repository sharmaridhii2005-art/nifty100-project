from fastapi import APIRouter
import pandas as pd

router = APIRouter(
    prefix="/valuation",
    tags=["Valuation"]
)

VALUATION_FILE = "output/valuation_flags.csv"


@router.get("")
def get_valuation():
    df = pd.read_csv(VALUATION_FILE)

    return {
        "count": len(df),
        "valuations": df.to_dict(orient="records")
    }


@router.get("/{company_id}")
def get_company_valuation(company_id: str):
    df = pd.read_csv(VALUATION_FILE)

    result = df[
        df["company_id"].str.upper() == company_id.upper()
    ]

    if result.empty:
        return {
            "error": "Valuation data not found",
            "company_id": company_id
        }

    return result.iloc[0].to_dict()