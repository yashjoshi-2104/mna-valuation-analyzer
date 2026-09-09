"""
ETL pipeline: raw CSVs -> validated, cleaned data -> DuckDB.

Stages: ingest -> validate -> clean -> transform (derive market cap / EV) -> load.
Run directly: python -m src.ingestion.load_data
"""
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.database.db import reset_database, get_connection  # noqa: E402

RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


class DataQualityError(Exception):
    pass


def _validate_companies(df: pd.DataFrame) -> list[str]:
    issues = []
    required = ["company_id", "name", "revenue_musd", "shares_outstanding_m", "share_price_usd"]
    for col in required:
        if col not in df.columns:
            issues.append(f"Missing required column: {col}")
    if df["company_id"].duplicated().any():
        dupes = df.loc[df["company_id"].duplicated(), "company_id"].tolist()
        issues.append(f"Duplicate company_id values: {dupes}")
    if (df["revenue_musd"] <= 0).any():
        issues.append("Found non-positive revenue values")
    if df[required].isna().any().any():
        issues.append("Found missing values in required columns")
    return issues


def _validate_transactions(df: pd.DataFrame) -> list[str]:
    issues = []
    if df["deal_id"].duplicated().any():
        issues.append("Duplicate deal_id values found")
    if (df["deal_value_musd"] <= 0).any():
        issues.append("Found non-positive deal values")
    return issues


def load_companies() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "companies.csv")
    issues = _validate_companies(df)
    if issues:
        raise DataQualityError("; ".join(issues))

    # Deduplicate defensively even though validation already checked
    df = df.drop_duplicates(subset="company_id")

    # Derived fields: market cap, enterprise value, key ratios
    df["market_cap_musd"] = df["shares_outstanding_m"] * df["share_price_usd"]
    df["enterprise_value_musd"] = (
        df["market_cap_musd"] + df["total_debt_musd"] - df["cash_musd"]
    )
    return df


def load_transactions() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "transactions.csv", parse_dates=["announce_date"])
    issues = _validate_transactions(df)
    if issues:
        raise DataQualityError("; ".join(issues))
    df = df.drop_duplicates(subset="deal_id")
    # ev_ebitda of "NM" (not meaningful, negative EBITDA) already excluded upstream;
    # coerce any stray non-numeric values to NaN rather than silently dropping rows.
    df["ev_ebitda"] = pd.to_numeric(df["ev_ebitda"], errors="coerce")
    return df


def run_etl() -> dict:
    """Full pipeline: reset DB, load + validate + transform, write to DuckDB."""
    companies = load_companies()
    transactions = load_transactions()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    companies.to_csv(PROCESSED_DIR / "companies_clean.csv", index=False)
    transactions.to_csv(PROCESSED_DIR / "transactions_clean.csv", index=False)

    reset_database()
    con = get_connection()

    # Register with names distinct from the target tables — otherwise DuckDB's
    # replacement scan resolves the bare table name to the (empty) DB table
    # instead of the in-memory DataFrame.
    con.register("companies_df", companies)
    con.register("transactions_df", transactions)

    con.execute(
        "INSERT INTO companies SELECT company_id, name, ticker, industry, sector, geography FROM companies_df"
    )
    con.execute(
        """INSERT INTO financials
           SELECT company_id, revenue_musd, revenue_growth_pct, ebitda_musd,
                  net_income_musd, total_debt_musd, cash_musd FROM companies_df"""
    )
    con.execute(
        """INSERT INTO market_data
           SELECT company_id, shares_outstanding_m, share_price_usd,
                  market_cap_musd, enterprise_value_musd FROM companies_df"""
    )
    con.execute(
        """INSERT INTO transactions
           SELECT deal_id, acquirer, target, announce_date, deal_value_musd, industry,
                  target_revenue_musd, target_ebitda_musd, ev_revenue, ev_ebitda,
                  geography, deal_type FROM transactions_df"""
    )
    con.close()

    return {"companies_loaded": len(companies), "transactions_loaded": len(transactions)}


if __name__ == "__main__":
    result = run_etl()
    print(f"ETL complete: {result}")
