import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.valuation.engine import (
    trading_comps_valuation,
    precedent_transactions_valuation,
    blend_valuation,
)


def test_trading_comps_basic():
    result = trading_comps_valuation(
        target_revenue_musd=1000,
        target_ebitda_musd=200,
        peer_ev_revenue=[4, 5, 6, 7, 8],
        peer_ev_ebitda=[15, 18, 20, 22, 25],
    )
    assert result.base_ev_musd is not None
    assert result.low_ev_musd < result.base_ev_musd < result.high_ev_musd


def test_trading_comps_negative_ebitda_excludes_ebitda_multiple():
    result = trading_comps_valuation(
        target_revenue_musd=1000,
        target_ebitda_musd=-50,
        peer_ev_revenue=[4, 5, 6],
        peer_ev_ebitda=[15, 18, 20],
    )
    assert "EV/EBITDA excluded" in result.notes
    # Should still produce a revenue-multiple-only estimate
    assert result.base_ev_musd is not None


def test_precedent_transactions_basic():
    result = precedent_transactions_valuation(
        target_revenue_musd=500,
        target_ebitda_musd=100,
        deal_ev_revenue=[6, 8, 10],
        deal_ev_ebitda=[20, 25, 30],
    )
    assert result.method == "Precedent Transactions"
    assert result.base_ev_musd is not None


def test_blend_valuation_reconciles_methods():
    r1 = trading_comps_valuation(1000, 200, [4, 5, 6], [15, 18, 20])
    r2 = precedent_transactions_valuation(1000, 200, [6, 8, 10], [20, 25, 30])
    blended = blend_valuation([r1, r2])
    assert blended["low_ev_musd"] <= blended["base_ev_musd"] <= blended["high_ev_musd"]
    assert len(blended["methods"]) == 2
    assert "not investment advice" in blended["disclaimer"]


def test_blend_valuation_handles_empty_input():
    blended = blend_valuation([])
    assert blended["low_ev_musd"] is None
    assert blended["methods"] == []
