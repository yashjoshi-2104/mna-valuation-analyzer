"""
Export a Power-BI-ready snapshot of the analyzed data.

Power BI Desktop can't query our Python calculation layer directly, so this
script runs the same deterministic calculations used by the API and writes
flat CSVs that Power BI's "Get Data > Text/CSV" (or Folder) connector can
load directly — no ODBC driver, no DuckDB extension required on the Power BI
side, which keeps this ₹0 and dependency-free.

Run: python -m src.export.powerbi_export
Output: powerbi/data/*.csv
"""
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.database.db import get_connection  # noqa: E402
from src.analytics.financials import compute_metrics_for_row  # noqa: E402

OUT_DIR = ROOT / "powerbi" / "data"


def export_company_metrics(con) -> pd.DataFrame:
    df = con.execute(
        """
        SELECT c.company_id, c.name, c.ticker, c.industry, c.sector, c.geography,
               f.revenue_musd, f.revenue_growth_pct, f.ebitda_musd, f.net_income_musd,
               f.total_debt_musd, f.cash_musd, m.market_cap_musd
        FROM companies c
        JOIN financials f USING (company_id)
        JOIN market_data m USING (company_id)
        """
    ).fetchdf()

    rows = []
    for _, row in df.iterrows():
        metrics = compute_metrics_for_row(row.to_dict())
        rec = metrics.as_dict()
        rec["ticker"] = row["ticker"]
        rec["industry"] = row["industry"]
        rec["sector"] = row["sector"]
        rec["geography"] = row["geography"]
        rows.append(rec)

    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "company_metrics.csv", index=False)
    return out


def export_transactions(con) -> pd.DataFrame:
    df = con.execute("SELECT * FROM transactions ORDER BY announce_date DESC").fetchdf()
    df.to_csv(OUT_DIR / "transactions.csv", index=False)
    return df


def export_transaction_summary_by_industry(con) -> pd.DataFrame:
    df = con.execute(
        """
        SELECT
            industry,
            count(*)                          AS deal_count,
            median(ev_revenue)                AS median_ev_revenue,
            median(ev_ebitda)                 AS median_ev_ebitda,
            quantile_cont(ev_revenue, 0.25)    AS p25_ev_revenue,
            quantile_cont(ev_revenue, 0.75)    AS p75_ev_revenue
        FROM transactions
        GROUP BY industry
        """
    ).fetchdf()
    df.to_csv(OUT_DIR / "transaction_summary_by_industry.csv", index=False)
    return df


def run_export() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = get_connection(read_only=True)
    try:
        metrics = export_company_metrics(con)
        txns = export_transactions(con)
        summary = export_transaction_summary_by_industry(con)
    finally:
        con.close()
    return {
        "company_metrics_rows": len(metrics),
        "transactions_rows": len(txns),
        "industry_summary_rows": len(summary),
        "output_dir": str(OUT_DIR),
    }


if __name__ == "__main__":
    result = run_export()
    print(f"Power BI export complete: {result}")
