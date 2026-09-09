from fastapi import APIRouter, Depends
import pandas as pd

from backend.deps import get_cursor, query_df
from src.analytics.financials import summary_stats

router = APIRouter()


@router.get("")
def list_transactions(cur=Depends(get_cursor)):
    df = query_df(cur, "SELECT * FROM transactions ORDER BY announce_date DESC")
    df["announce_date"] = df["announce_date"].astype(str)
    # ev_ebitda is NaN for deals with negative/zero target EBITDA (economically
    # "not meaningful", not missing data) — NaN isn't valid JSON, so convert to
    # None and let the frontend render it as "NM".
    df = df.astype(object).where(pd.notnull(df), None)
    return df.to_dict(orient="records")


@router.get("/summary")
def transactions_summary(cur=Depends(get_cursor)):
    df = query_df(cur, "SELECT ev_revenue, ev_ebitda FROM transactions")
    return {
        "ev_revenue": summary_stats(df["ev_revenue"].tolist()),
        "ev_ebitda": summary_stats(df["ev_ebitda"].tolist()),
        "deal_count": len(df),
    }
