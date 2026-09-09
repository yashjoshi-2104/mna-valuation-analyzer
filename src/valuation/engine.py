"""
Valuation engine.

Two independent methods, each producing an implied enterprise value range,
then blended into a single Low/Base/High. Every number here is traceable:
    raw data -> calculated multiple -> applied multiple -> implied value.
Nothing here is a guarantee — outputs are always labeled as estimates.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from src.analytics.financials import summary_stats


@dataclass
class ValuationResult:
    method: str
    low_ev_musd: float | None
    base_ev_musd: float | None
    high_ev_musd: float | None
    multiple_stats: dict = field(default_factory=dict)
    notes: str = ""


def trading_comps_valuation(
    target_revenue_musd: float,
    target_ebitda_musd: float | None,
    peer_ev_revenue: list[float],
    peer_ev_ebitda: list[float],
) -> ValuationResult:
    rev_stats = summary_stats(peer_ev_revenue)
    ebitda_stats = summary_stats(peer_ev_ebitda)

    # Revenue-multiple-implied EV
    rev_low = (rev_stats["p25"] or 0) * target_revenue_musd if rev_stats["n"] else None
    rev_base = (rev_stats["median"] or 0) * target_revenue_musd if rev_stats["n"] else None
    rev_high = (rev_stats["p75"] or 0) * target_revenue_musd if rev_stats["n"] else None

    # EBITDA-multiple-implied EV (only meaningful if target EBITDA is positive)
    ebitda_low = ebitda_high = ebitda_base = None
    if target_ebitda_musd and target_ebitda_musd > 0 and ebitda_stats["n"]:
        ebitda_low = (ebitda_stats["p25"] or 0) * target_ebitda_musd
        ebitda_base = (ebitda_stats["median"] or 0) * target_ebitda_musd
        ebitda_high = (ebitda_stats["p75"] or 0) * target_ebitda_musd

    lows = [v for v in (rev_low, ebitda_low) if v is not None]
    bases = [v for v in (rev_base, ebitda_base) if v is not None]
    highs = [v for v in (rev_high, ebitda_high) if v is not None]

    notes = "Blends EV/Revenue and EV/EBITDA peer multiples (25th/median/75th pctile)."
    if ebitda_low is None:
        notes += " EV/EBITDA excluded: target EBITDA is zero or negative."

    return ValuationResult(
        method="Trading Comps",
        low_ev_musd=round(sum(lows) / len(lows), 1) if lows else None,
        base_ev_musd=round(sum(bases) / len(bases), 1) if bases else None,
        high_ev_musd=round(sum(highs) / len(highs), 1) if highs else None,
        multiple_stats={"ev_revenue": rev_stats, "ev_ebitda": ebitda_stats},
        notes=notes,
    )


def precedent_transactions_valuation(
    target_revenue_musd: float,
    target_ebitda_musd: float | None,
    deal_ev_revenue: list[float],
    deal_ev_ebitda: list[float],
) -> ValuationResult:
    rev_stats = summary_stats(deal_ev_revenue)
    ebitda_stats = summary_stats(deal_ev_ebitda)

    rev_low = (rev_stats["p25"] or 0) * target_revenue_musd if rev_stats["n"] else None
    rev_base = (rev_stats["median"] or 0) * target_revenue_musd if rev_stats["n"] else None
    rev_high = (rev_stats["p75"] or 0) * target_revenue_musd if rev_stats["n"] else None

    ebitda_low = ebitda_high = ebitda_base = None
    if target_ebitda_musd and target_ebitda_musd > 0 and ebitda_stats["n"]:
        ebitda_low = (ebitda_stats["p25"] or 0) * target_ebitda_musd
        ebitda_base = (ebitda_stats["median"] or 0) * target_ebitda_musd
        ebitda_high = (ebitda_stats["p75"] or 0) * target_ebitda_musd

    lows = [v for v in (rev_low, ebitda_low) if v is not None]
    bases = [v for v in (rev_base, ebitda_base) if v is not None]
    highs = [v for v in (rev_high, ebitda_high) if v is not None]

    return ValuationResult(
        method="Precedent Transactions",
        low_ev_musd=round(sum(lows) / len(lows), 1) if lows else None,
        base_ev_musd=round(sum(bases) / len(bases), 1) if bases else None,
        high_ev_musd=round(sum(highs) / len(highs), 1) if highs else None,
        multiple_stats={"ev_revenue": rev_stats, "ev_ebitda": ebitda_stats},
        notes=(
            "Historical change-of-control multiples typically embed a control "
            "premium — this range is not directly comparable to public trading levels."
        ),
    )


def blend_valuation(results: list[ValuationResult]) -> dict:
    """Reconcile multiple method outputs into one Low/Base/High range."""
    lows = [r.low_ev_musd for r in results if r.low_ev_musd is not None]
    bases = [r.base_ev_musd for r in results if r.base_ev_musd is not None]
    highs = [r.high_ev_musd for r in results if r.high_ev_musd is not None]

    return {
        "low_ev_musd": round(min(lows), 1) if lows else None,
        "base_ev_musd": round(sum(bases) / len(bases), 1) if bases else None,
        "high_ev_musd": round(max(highs), 1) if highs else None,
        "methods": [
            {
                "method": r.method,
                "low_ev_musd": r.low_ev_musd,
                "base_ev_musd": r.base_ev_musd,
                "high_ev_musd": r.high_ev_musd,
                "notes": r.notes,
            }
            for r in results
        ],
        "disclaimer": (
            "This is an educational analytical estimate, not investment advice. "
            "Ranges are derived from a small, static comp/transaction set and "
            "should not be relied on for actual deal decisions."
        ),
    }
