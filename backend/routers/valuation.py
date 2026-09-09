from fastapi import APIRouter, Depends, HTTPException, Query

from backend.deps import get_cursor, query_df
from src.ml.comps import find_comparables
from src.valuation.engine import (
    trading_comps_valuation,
    precedent_transactions_valuation,
    blend_valuation,
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


@router.get("/{company_id}")
def get_valuation(company_id: str, top_n_peers: int = Query(5, ge=2, le=15), cur=Depends(get_cursor)):
    universe = _universe(cur)
    if company_id not in universe["company_id"].values:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")

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
        target_revenue_musd=float(target["revenue_musd"]),
        target_ebitda_musd=float(target["ebitda_musd"]),
        peer_ev_revenue=peer_ev_revenue,
        peer_ev_ebitda=peer_ev_ebitda,
    )

    deals = query_df(cur, "SELECT ev_revenue, ev_ebitda FROM transactions WHERE industry = ?", [target["industry"]])
    precedent = precedent_transactions_valuation(
        target_revenue_musd=float(target["revenue_musd"]),
        target_ebitda_musd=float(target["ebitda_musd"]),
        deal_ev_revenue=deals["ev_revenue"].dropna().tolist(),
        deal_ev_ebitda=deals["ev_ebitda"].dropna().tolist(),
    )

    blended = blend_valuation([trading, precedent])

    return {
        "target": {
            "company_id": target["company_id"],
            "name": target["name"],
            "revenue_musd": float(target["revenue_musd"]),
            "ebitda_musd": float(target["ebitda_musd"]),
            "current_enterprise_value_musd": float(target["enterprise_value_musd"]),
        },
        "peers_used": peers[["company_id", "name", "similarity_score"]].to_dict(orient="records"),
        "valuation": blended,
    }
