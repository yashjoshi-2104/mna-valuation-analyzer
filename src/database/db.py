"""
DuckDB connection and schema management.

The database is a single embedded file at data/processed/mna.duckdb.
No server, no credentials — this is intentional: DuckDB gives us real SQL
with zero infrastructure cost.

Connection strategy: the API layer opens ONE shared read-only connection at
startup (see backend/main.py lifespan) and hands out cheap `.cursor()`
handles per request rather than opening/closing a fresh file connection on
every single API call. Repeatedly opening the DuckDB file from many
concurrent requests was the root cause of intermittent connection failures
under load — cursors share the same open file handle and are safe to use
concurrently from FastAPI's threadpool.
"""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "processed" / "mna.duckdb"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"


def get_connection(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH), read_only=read_only)


def init_schema(con: duckdb.DuckDBPyConnection) -> None:
    ddl = SCHEMA_PATH.read_text()
    con.execute(ddl)


def reset_database() -> None:
    """Drop and recreate the DB file from scratch. Used by the ETL pipeline."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = get_connection()
    init_schema(con)
    con.close()
