from fastapi import APIRouter, Depends, HTTPException, Query
import pandas as pd

from backend.deps import get_cursor, query_df
from src.ml.comps import find_comparables

router = APIRouter()


@router.get("/{company_id}")
def get_comparables(company_id: str, top_n: int = Query(5, ge=1, le=15), cur=Depends(get_cursor)):
    df = query_df(cur, """
        SELECT c.company_id, c.name, c.industry,
               f.revenue_musd, f.revenue_growth_pct, f.ebitda_musd,
               f.total_debt_musd,
               m.market_cap_musd, m.enterprise_value_musd
        FROM companies c
        JOIN financials f USING (company_id)
        JOIN market_data m USING (company_id)
    """)
    if company_id not in df["company_id"].values:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")

    df["ebitda_margin_pct"] = (df["ebitda_musd"] / df["revenue_musd"] * 100).round(2)
    df["debt_to_ebitda"] = df.apply(
        lambda r: round(r["total_debt_musd"] / r["ebitda_musd"], 2) if r["ebitda_musd"] > 0 else None,
        axis=1,
    )

    result = find_comparables(df, company_id, top_n=top_n)
    # debt_to_ebitda is NaN (not just None) for any peer with negative/zero
    # EBITDA (e.g. Snowflake) once the column round-trips through pandas as
    # float64 — NaN isn't valid JSON, so any peer set that includes such a
    # company crashed with a 500. Same fix already applied in transactions.py.
    result = result.astype(object).where(pd.notnull(result), None)
    return result.to_dict(orient="records")
