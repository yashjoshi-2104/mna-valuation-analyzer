from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_cursor, query_df
from src.analytics.financials import compute_metrics_for_row

router = APIRouter()


@router.get("")
def list_companies(cur=Depends(get_cursor)):
    df = query_df(cur, """
        SELECT c.company_id, c.name, c.ticker, c.industry, c.sector, c.geography,
               f.revenue_musd, f.revenue_growth_pct, f.ebitda_musd, f.net_income_musd,
               f.total_debt_musd, f.cash_musd,
               m.market_cap_musd, m.enterprise_value_musd
        FROM companies c
        JOIN financials f USING (company_id)
        JOIN market_data m USING (company_id)
        ORDER BY c.name
    """)
    return df.to_dict(orient="records")


@router.get("/{company_id}")
def get_company(company_id: str, cur=Depends(get_cursor)):
    df = query_df(cur, """
        SELECT c.company_id, c.name, c.ticker, c.industry, c.sector, c.geography,
               f.revenue_musd, f.revenue_growth_pct, f.ebitda_musd, f.net_income_musd,
               f.total_debt_musd, f.cash_musd,
               m.market_cap_musd, m.enterprise_value_musd
        FROM companies c
        JOIN financials f USING (company_id)
        JOIN market_data m USING (company_id)
        WHERE c.company_id = ?
    """, [company_id])
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
    return df.iloc[0].to_dict()


@router.get("/{company_id}/metrics")
def get_company_metrics(company_id: str, cur=Depends(get_cursor)):
    """Deterministic financial ratios and EV - pure Python calculation, no ML."""
    df = query_df(cur, """
        SELECT c.company_id, c.name, f.revenue_musd, f.ebitda_musd, f.net_income_musd,
               f.total_debt_musd, f.cash_musd, m.market_cap_musd
        FROM companies c
        JOIN financials f USING (company_id)
        JOIN market_data m USING (company_id)
        WHERE c.company_id = ?
    """, [company_id])
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
    metrics = compute_metrics_for_row(df.iloc[0].to_dict())
    return metrics.as_dict()
