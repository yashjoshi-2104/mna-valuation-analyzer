"""
Deterministic financial calculations.

These are pure arithmetic — no ML, no LLM. Anything that touches an actual
dollar figure lives here so it stays auditable and testable.
"""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass
class CompanyMetrics:
    company_id: str
    name: str
    revenue_musd: float
    ebitda_musd: float
    net_income_musd: float
    total_debt_musd: float
    cash_musd: float
    market_cap_musd: float

    @property
    def enterprise_value_musd(self) -> float:
        return self.market_cap_musd + self.total_debt_musd - self.cash_musd

    @property
    def ebitda_margin_pct(self) -> float | None:
        if self.revenue_musd == 0:
            return None
        return round(100 * self.ebitda_musd / self.revenue_musd, 2)

    @property
    def debt_to_ebitda(self) -> float | None:
        if self.ebitda_musd is None or self.ebitda_musd <= 0:
            return None  # not meaningful for negative/zero EBITDA
        return round(self.total_debt_musd / self.ebitda_musd, 2)

    @property
    def pe_ratio(self) -> float | None:
        if self.net_income_musd is None or self.net_income_musd <= 0:
            return None  # not meaningful for a loss-making company
        return round(self.market_cap_musd / self.net_income_musd, 2)

    @property
    def ev_revenue(self) -> float | None:
        if self.revenue_musd == 0:
            return None
        return round(self.enterprise_value_musd / self.revenue_musd, 2)

    @property
    def ev_ebitda(self) -> float | None:
        if self.ebitda_musd is None or self.ebitda_musd <= 0:
            return None  # not meaningful for negative/zero EBITDA
        return round(self.enterprise_value_musd / self.ebitda_musd, 2)

    def as_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "name": self.name,
            "revenue_musd": self.revenue_musd,
            "ebitda_musd": self.ebitda_musd,
            "net_income_musd": self.net_income_musd,
            "market_cap_musd": round(self.market_cap_musd, 1),
            "enterprise_value_musd": round(self.enterprise_value_musd, 1),
            "ebitda_margin_pct": self.ebitda_margin_pct,
            "debt_to_ebitda": self.debt_to_ebitda,
            "pe_ratio": self.pe_ratio,
            "ev_revenue": self.ev_revenue,
            "ev_ebitda": self.ev_ebitda,
        }


def compute_metrics_for_row(row: dict) -> CompanyMetrics:
    return CompanyMetrics(
        company_id=row["company_id"],
        name=row["name"],
        revenue_musd=row["revenue_musd"],
        ebitda_musd=row["ebitda_musd"],
        net_income_musd=row["net_income_musd"],
        total_debt_musd=row["total_debt_musd"],
        cash_musd=row["cash_musd"],
        market_cap_musd=row["market_cap_musd"],
    )


def percentile(values: list[float], pct: float) -> float | None:
    """Simple linear-interpolation percentile, avoids pulling in numpy for one function."""
    clean = sorted(v for v in values if v is not None and not math.isnan(v))
    if not clean:
        return None
    if len(clean) == 1:
        return clean[0]
    k = (len(clean) - 1) * (pct / 100)
    f, c = math.floor(k), math.ceil(k)
    if f == c:
        return clean[int(k)]
    return clean[f] + (clean[c] - clean[f]) * (k - f)


def summary_stats(values: list[float]) -> dict:
    clean = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if not clean:
        return {"mean": None, "median": None, "min": None, "max": None, "p25": None, "p75": None, "n": 0}
    return {
        "mean": round(sum(clean) / len(clean), 2),
        "median": percentile(clean, 50),
        "min": min(clean),
        "max": max(clean),
        "p25": percentile(clean, 25),
        "p75": percentile(clean, 75),
        "n": len(clean),
    }
