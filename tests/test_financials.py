import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analytics.financials import CompanyMetrics, percentile, summary_stats


def make_metrics(**overrides) -> CompanyMetrics:
    base = dict(
        company_id="X1",
        name="Test Co",
        revenue_musd=1000,
        ebitda_musd=200,
        net_income_musd=100,
        total_debt_musd=300,
        cash_musd=100,
        market_cap_musd=5000,
    )
    base.update(overrides)
    return CompanyMetrics(**base)


def test_enterprise_value():
    m = make_metrics(market_cap_musd=5000, total_debt_musd=300, cash_musd=100)
    assert m.enterprise_value_musd == 5200


def test_ebitda_margin():
    m = make_metrics(revenue_musd=1000, ebitda_musd=250)
    assert m.ebitda_margin_pct == 25.0


def test_ev_ebitda_negative_ebitda_is_not_meaningful():
    m = make_metrics(ebitda_musd=-50)
    assert m.ev_ebitda is None
    assert m.debt_to_ebitda is None


def test_ev_ebitda_zero_ebitda_is_not_meaningful():
    m = make_metrics(ebitda_musd=0)
    assert m.ev_ebitda is None


def test_pe_ratio_negative_net_income_is_not_meaningful():
    m = make_metrics(net_income_musd=-10)
    assert m.pe_ratio is None


def test_ev_revenue_zero_revenue():
    m = make_metrics(revenue_musd=0)
    assert m.ev_revenue is None
    assert m.ebitda_margin_pct is None


def test_percentile_matches_known_values():
    values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert percentile(values, 50) == 5.5
    assert percentile(values, 25) == 3.25
    assert percentile(values, 75) == 7.75


def test_percentile_empty_list():
    assert percentile([], 50) is None


def test_summary_stats_ignores_none_and_nan():
    stats = summary_stats([10, None, 20, float("nan"), 30])
    assert stats["n"] == 3
    assert stats["mean"] == 20.0
    assert stats["median"] == 20.0
