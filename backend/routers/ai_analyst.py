from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.deps import get_cursor, query_df
from src.ml.comps import find_comparables
from src.valuation.engine import (
    trading_comps_valuation,
    precedent_transactions_valuation,
    blend_valuation,
)
from src.analytics.financials import compute_metrics_for_row
from src.ai.explain import (
    explain_comparables,
    explain_valuation,
    build_context_block,
    chat as ollama_chat,
    chat_stream as ollama_chat_stream,
    OllamaUnavailable,
    MODEL,
)

router = APIRouter()


def _universe(cur):
    df = query_df(cur, """
        SELECT c.company_id, c.name, c.industry,
               f.revenue_musd, f.revenue_growth_pct, f.ebitda_musd,
               f.total_debt_musd,
               m.market_cap_musd, m.enterprise_value_musd
        FROM companies c
        JOIN financials f USING (company_id)
        JOIN market_data m USING (company_id)
    """)
    df["ebitda_margin_pct"] = (df["ebitda_musd"] / df["revenue_musd"] * 100).round(2)
    df["debt_to_ebitda"] = df.apply(
        lambda r: round(r["total_debt_musd"] / r["ebitda_musd"], 2) if r["ebitda_musd"] > 0 else None,
        axis=1,
    )
    return df


def _valuation_for(cur, universe, company_id, top_n_peers=5):
    target = universe[universe["company_id"] == company_id].iloc[0]
    peers = find_comparables(universe, company_id, top_n=top_n_peers)
    peer_rows = universe[universe["company_id"].isin(peers["company_id"])]

    peer_ev_revenue = (peer_rows["enterprise_value_musd"] / peer_rows["revenue_musd"]).round(2).tolist()
    peer_ev_ebitda = [
        round(r["enterprise_value_musd"] / r["ebitda_musd"], 2)
        for _, r in peer_rows.iterrows()
        if r["ebitda_musd"] and r["ebitda_musd"] > 0
    ]
    trading = trading_comps_valuation(
        float(target["revenue_musd"]), float(target["ebitda_musd"]), peer_ev_revenue, peer_ev_ebitda
    )
    deals = query_df(cur, "SELECT ev_revenue, ev_ebitda FROM transactions WHERE industry = ?", [target["industry"]])
    precedent = precedent_transactions_valuation(
        float(target["revenue_musd"]),
        float(target["ebitda_musd"]),
        deals["ev_revenue"].dropna().tolist(),
        deals["ev_ebitda"].dropna().tolist(),
    )
    blended = blend_valuation([trading, precedent])
    return target, peers, blended


def _build_chat_context(cur, universe, company_id):
    """Shared by both /chat and /chat/stream so the two stay identical."""
    row = universe[universe["company_id"] == company_id].iloc[0]
    full = query_df(cur, """
        SELECT c.company_id, c.name, f.revenue_musd, f.ebitda_musd, f.net_income_musd,
               f.total_debt_musd, f.cash_musd, m.market_cap_musd
        FROM companies c
        JOIN financials f USING (company_id)
        JOIN market_data m USING (company_id)
        WHERE c.company_id = ?
    """, [company_id]).iloc[0]
    metrics = compute_metrics_for_row(full.to_dict()).as_dict()

    target, peers, blended = _valuation_for(cur, universe, company_id)
    peers_merged = peers.merge(universe[["company_id", "revenue_musd"]], on="company_id", suffixes=("", "_u"))
    return build_context_block(row["name"], metrics, peers_merged.to_dict(orient="records"), blended)


@router.get("/comps/{company_id}")
def explain_comps_endpoint(company_id: str, top_n: int = Query(5, ge=1, le=15), cur=Depends(get_cursor)):
    universe = _universe(cur)
    if company_id not in universe["company_id"].values:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")

    target_name = universe.loc[universe["company_id"] == company_id, "name"].iloc[0]
    peers = find_comparables(universe, company_id, top_n=top_n)

    try:
        explanation = explain_comparables(
            target_name, peers[["name", "similarity_score"]].to_dict(orient="records")
        )
    except OllamaUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {"target": target_name, "explanation": explanation, "model": MODEL}


@router.get("/valuation/{company_id}")
def explain_valuation_endpoint(company_id: str, top_n_peers: int = Query(5, ge=2, le=15), cur=Depends(get_cursor)):
    universe = _universe(cur)
    if company_id not in universe["company_id"].values:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")

    target, peers, blended = _valuation_for(cur, universe, company_id, top_n_peers)

    try:
        explanation = explain_valuation(target["name"], blended)
    except OllamaUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {"target": target["name"], "explanation": explanation, "model": MODEL}


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    company_id: str
    messages: list[ChatMessage]


@router.post("/chat")
def chat_endpoint(req: ChatRequest, cur=Depends(get_cursor)):
    """Non-streaming variant - waits for the full reply. Prefer /chat/stream
    from the UI; this is kept for simple scripted/API use."""
    universe = _universe(cur)
    if req.company_id not in universe["company_id"].values:
        raise HTTPException(status_code=404, detail=f"Company {req.company_id} not found")
    if not req.messages:
        raise HTTPException(status_code=422, detail="messages cannot be empty")

    context = _build_chat_context(cur, universe, req.company_id)

    try:
        reply = ollama_chat(context, [m.model_dump() for m in req.messages])
    except OllamaUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {"reply": reply, "model": MODEL}


@router.post("/chat/stream")
def chat_stream_endpoint(req: ChatRequest, cur=Depends(get_cursor)):
    """
    Streams the reply as plain text chunks as the model generates them.
    This is what the frontend uses - it fixes the "replying very late" feel
    by showing text within a second or two instead of one long silent wait.
    """
    universe = _universe(cur)
    if req.company_id not in universe["company_id"].values:
        raise HTTPException(status_code=404, detail=f"Company {req.company_id} not found")
    if not req.messages:
        raise HTTPException(status_code=422, detail="messages cannot be empty")

    context = _build_chat_context(cur, universe, req.company_id)
    messages = [m.model_dump() for m in req.messages]

    def gen():
        try:
            for chunk in ollama_chat_stream(context, messages):
                yield chunk
        except OllamaUnavailable as e:
            # Mid-stream failure (e.g. Ollama restarted) - surface it as
            # readable text since headers are already sent at this point.
            yield f"\n\n[Error: {e}]"

    return StreamingResponse(gen(), media_type="text/plain")
