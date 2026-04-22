from __future__ import annotations

from typing import Any
import pandas as pd

from src.phase1.retrieval.recommend import UserPrefs, recommend_from_df


def build_response(*, request_id: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    return {"request_id": request_id, "results": results}


def deterministic_results(df: pd.DataFrame, prefs: UserPrefs) -> list[dict[str, Any]]:
    """Phase 1-style ranking + shape expected by POST /recommendations."""
    return recommend_from_df(df, prefs)
