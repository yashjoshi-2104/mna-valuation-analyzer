"""
Shared DB dependency for routers.

Design: one long-lived read-only DuckDB connection is opened at app startup
(backend/main.py lifespan) and stored on `app.state.db`. Each request gets a
lightweight `.cursor()` off that connection rather than opening a brand-new
file connection per call - cursors are cheap, safe to use from FastAPI's
threadpool concurrently, and this avoids the file-handle churn that caused
intermittent request failures under concurrent load.
"""
from fastapi import Request
import pandas as pd


def get_cursor(request: Request):
    """FastAPI dependency: yields a fresh cursor off the shared connection."""
    con = request.app.state.db
    cur = con.cursor()
    try:
        yield cur
    finally:
        cur.close()


def query_df(cur, sql: str, params: list | None = None) -> pd.DataFrame:
    """Run a SQL query on the given cursor and return a pandas DataFrame."""
    return cur.execute(sql, params or []).fetchdf()
