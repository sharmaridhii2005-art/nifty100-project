from fastapi import APIRouter
from app.utils.database import get_connection

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("")
def get_companies():
    conn = get_connection()

    rows = conn.execute("""
        SELECT
            id,
            company_name,
            face_value,
            book_value,
            roce_percentage,
            roe_percentage
        FROM companies
        ORDER BY company_name
    """).fetchall()

    conn.close()

    return {
        "count": len(rows),
        "companies": [dict(row) for row in rows]
    }


@router.get("/{company_id}")
def get_company(company_id: str):
    conn = get_connection()

    row = conn.execute("""
        SELECT
            id,
            company_name,
            face_value,
            book_value,
            roce_percentage,
            roe_percentage
        FROM companies
        WHERE id = ?
    """, (company_id,)).fetchone()

    conn.close()

    if row is None:
        return {
            "error": "Company not found",
            "company_id": company_id
        }

    return dict(row)