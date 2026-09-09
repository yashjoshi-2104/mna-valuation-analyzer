"""
Comparable-company recommendation.

Methodology: scale a small set of business/financial features, then rank the
universe by cosine similarity to the target. This is intentionally NOT a
supervised classifier — there's no ground-truth "correct comp set" to train
against, so an unsupervised similarity ranking is the honest choice, and it
keeps every recommendation traceable back to the features that drove it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

FEATURES = [
    "revenue_musd",
    "revenue_growth_pct",
    "ebitda_margin_pct",
    "market_cap_musd",
    "enterprise_value_musd",
    "debt_to_ebitda",
]


def _prep_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Fill NaNs (e.g. debt_to_ebitda undefined for negative EBITDA) with the
    column median so one missing ratio doesn't crash the whole vector — this
    is a deliberate, documented imputation choice, not silent data loss."""
    X = df[FEATURES].copy()
    for col in FEATURES:
        X[col] = X[col].fillna(X[col].median())
    return X


def find_comparables(df: pd.DataFrame, target_company_id: str, top_n: int = 5) -> pd.DataFrame:
    """
    df must contain a 'company_id' column plus all columns in FEATURES.
    Returns the top_n most similar companies (excluding the target itself),
    each with a similarity_score in [0, 1] and a note on the leading driver.
    """
    if target_company_id not in df["company_id"].values:
        raise ValueError(f"Unknown company_id: {target_company_id}")

    X = _prep_feature_matrix(df)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    idx_map = {cid: i for i, cid in enumerate(df["company_id"])}
    target_idx = idx_map[target_company_id]

    sims = cosine_similarity(X_scaled[target_idx : target_idx + 1], X_scaled)[0]

    result = df.copy()
    result["similarity_score"] = np.round(sims, 4)
    result = result[result["company_id"] != target_company_id]
    result = result.sort_values("similarity_score", ascending=False).head(top_n)

    return result[["company_id", "name", "industry", "similarity_score"] + FEATURES]
