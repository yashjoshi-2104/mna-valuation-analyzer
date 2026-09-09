"""
M&A Valuation Analyzer - FastAPI backend.

Run: uvicorn backend.main:app --reload --port 8000  (from the project root)
"""
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from src.database.db import get_connection, DB_PATH
from backend.routers import companies, comps, transactions, valuation, ai_analyst

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("mna-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not DB_PATH.exists():
        logger.warning(
            "Database not found at %s - run `python -m src.ingestion.load_data` first.",
            DB_PATH,
        )
    # One shared read-only connection for the app's lifetime; routers pull
    # cheap per-request cursors off this instead of reopening the file.
    app.state.db = get_connection(read_only=True)
    logger.info("DuckDB connection opened: %s", DB_PATH)
    yield
    app.state.db.close()
    logger.info("DuckDB connection closed")


app = FastAPI(
    title="M&A Comparable Company & Valuation Analyzer API",
    description=(
        "Deterministic financial analytics, comparable-company similarity, "
        "and valuation range generation for a static software-sector comp universe. "
        "Educational use only - not investment advice."
    ),
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:4173", "http://127.0.0.1:4173",  # vite preview
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Any unhandled error becomes a clean JSON 500 instead of a dropped
    connection (which the browser reports as a confusing 'Failed to fetch').
    The real traceback still goes to the server log.
    """
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal error: {exc}"},
    )


app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(comps.router, prefix="/api/comps", tags=["comparable companies"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(valuation.router, prefix="/api/valuation", tags=["valuation"])
app.include_router(ai_analyst.router, prefix="/api/ai", tags=["ai analyst (optional)"])


@app.get("/api/health")
def health(request: Request):
    db_ok = True
    try:
        request.app.state.db.cursor().execute("SELECT 1").fetchone()
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": db_ok}
