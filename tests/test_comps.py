import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ml.comps import find_comparables


def sample_universe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            dict(company_id="A", name="Target", industry="Software",
                 revenue_musd=1000, revenue_growth_pct=20, ebitda_margin_pct=25,
                 market_cap_musd=8000, enterprise_value_musd=8200, debt_to_ebitda=1.0),
            dict(company_id="B", name="Close Peer", industry="Software",
                 revenue_musd=1050, revenue_growth_pct=19, ebitda_margin_pct=24,
                 market_cap_musd=8100, enterprise_value_musd=8300, debt_to_ebitda=1.1),
            dict(company_id="C", name="Distant Peer", industry="Software",
                 revenue_musd=50000, revenue_growth_pct=2, ebitda_margin_pct=45,
                 market_cap_musd=300000, enterprise_value_musd=310000, debt_to_ebitda=3.0),
            dict(company_id="D", name="Mid Peer", industry="Software",
                 revenue_musd=3000, revenue_growth_pct=15, ebitda_margin_pct=22,
                 market_cap_musd=20000, enterprise_value_musd=21000, debt_to_ebitda=1.5),
            dict(company_id="E", name="Missing Ratio Peer", industry="Software",
                 revenue_musd=1100, revenue_growth_pct=18, ebitda_margin_pct=20,
                 market_cap_musd=8500, enterprise_value_musd=8700, debt_to_ebitda=None),
        ]
    )


def test_excludes_target_from_results():
    df = sample_universe()
    result = find_comparables(df, "A", top_n=4)
    assert "A" not in result["company_id"].values


def test_closest_peer_ranks_first():
    df = sample_universe()
    result = find_comparables(df, "A", top_n=4)
    assert result.iloc[0]["company_id"] == "B"


def test_similarity_scores_are_bounded():
    df = sample_universe()
    result = find_comparables(df, "A", top_n=4)
    assert (result["similarity_score"] <= 1.0).all()
    assert (result["similarity_score"] >= -1.0).all()


def test_unknown_company_raises():
    df = sample_universe()
    try:
        find_comparables(df, "ZZZ")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_missing_ratio_does_not_crash():
    df = sample_universe()  # includes a row with debt_to_ebitda=None
    result = find_comparables(df, "A", top_n=4)
    assert len(result) == 4
