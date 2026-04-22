from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class UserPrefs:
    area: str
    budget_inr: float
    cuisine: str
    min_rating: float
    notes: str | None = None
    top_n: int = 5


def _norm(s: str) -> str:
    return " ".join(s.strip().split()).casefold()


def _area_match(area: str | None, user_area: str) -> bool:
    if not area:
        return False
    # Phase 1: area/locality exact match; later add fuzzy + nearby expansion.
    return _norm(area) == _norm(user_area)


def _cuisines_to_list(cuisines: Any) -> list[str]:
    """Parquet/Arrow may yield ndarray; API/JSON need plain lists."""
    if cuisines is None:
        return []
    if isinstance(cuisines, list):
        return [str(x).strip() for x in cuisines if str(x).strip()]
    try:
        return [str(x).strip() for x in list(cuisines) if str(x).strip()]
    except Exception:
        return []


def _cuisine_match(cuisines: list[str], user_cuisine: str) -> bool:
    uc = _norm(user_cuisine)
    try:
        return any(_norm(str(c)) == uc for c in cuisines)
    except TypeError:
        return False


def _budget_band(budget_inr: float) -> tuple[float, float]:
    # A forgiving band: ±30% with a minimum slack of ₹200.
    slack = max(200.0, 0.30 * budget_inr)
    lo = max(0.0, budget_inr - slack)
    hi = budget_inr + slack
    return lo, hi


def _score_row(*, rating: float, votes: int | None, cost: float | None, budget_inr: float) -> float:
    # Rating drives most of the score; cost closeness helps; votes break ties.
    rating_term = rating / 5.0
    votes_term = 0.0 if not votes else min(1.0, math.log10(max(1, votes)) / 4.0)

    if cost is None or budget_inr <= 0:
        cost_term = 0.0
        missing_cost_penalty = 0.05
    else:
        # Relative distance capped at 100%
        rel = abs(cost - budget_inr) / max(budget_inr, 1.0)
        cost_term = 1.0 - min(1.0, rel)
        missing_cost_penalty = 0.0

    return 0.70 * rating_term + 0.20 * cost_term + 0.10 * votes_term - missing_cost_penalty


def _reason(*, name: str, area: str | None, cuisines: list[str], rating: float, cost: float | None, prefs: UserPrefs) -> str:
    cost_str = f"₹{int(cost)} for two" if cost is not None else "cost not available"
    return (
        f"Matches {prefs.cuisine} in Bangalore ({area}), rating {rating:.1f} (min {prefs.min_rating:.1f}), "
        f"and is near your ₹{int(prefs.budget_inr)} budget ({cost_str})."
    )


def shortlist_from_df(df: pd.DataFrame, prefs: UserPrefs, *, k: int = 50) -> list[dict[str, Any]]:
    required_cols = {"id", "name", "city", "cuisines", "aggregate_rating", "avg_cost_for_two_inr", "votes"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing required columns: {sorted(missing)}")

    lo, hi = _budget_band(prefs.budget_inr)

    candidates: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        area = row.get("area", None)
        if not _area_match(area if isinstance(area, str) else str(area) if area is not None else None, prefs.area):
            continue

        cuisines_raw = row["cuisines"]
        cuisines = _cuisines_to_list(cuisines_raw)
        if not cuisines:
            continue
        if not _cuisine_match(cuisines, prefs.cuisine):
            continue

        rating = float(row["aggregate_rating"])
        if rating < prefs.min_rating:
            continue

        cost = row.get("avg_cost_for_two_inr", None)
        cost_f = None
        if cost is not None and not (isinstance(cost, float) and math.isnan(cost)):
            try:
                cost_f = float(cost)
            except Exception:
                cost_f = None

        # Cost is optional; if present, enforce budget band.
        if cost_f is not None and not (lo <= cost_f <= hi):
            continue

        votes = row.get("votes", None)
        votes_i = None
        try:
            if votes is not None and not (isinstance(votes, float) and math.isnan(votes)):
                votes_i = int(votes)
        except Exception:
            votes_i = None

        score = _score_row(rating=rating, votes=votes_i, cost=cost_f, budget_inr=prefs.budget_inr)
        candidates.append(
            {
                "restaurant_id": row["id"],
                "name": row["name"],
                "cuisines": cuisines,
                "rating": rating,
                "estimated_cost": cost_f if cost_f is not None else "N/A",
                "area": area if isinstance(area, str) else str(area) if area is not None else None,
                "reason": _reason(
                    name=row["name"],
                    area=area if isinstance(area, str) else str(area) if area is not None else None,
                    cuisines=cuisines,
                    rating=rating,
                    cost=cost_f,
                    prefs=prefs,
                ),
                "_score": score,
            }
        )

    candidates.sort(key=lambda x: (x["_score"], x["rating"]), reverse=True)
    return candidates[: max(1, int(k))]


def recommend_from_df(df: pd.DataFrame, prefs: UserPrefs) -> list[dict[str, Any]]:
    candidates = shortlist_from_df(df, prefs, k=max(50, int(prefs.top_n)))
    for c in candidates:
        c.pop("_score", None)
        c.pop("area", None)
    return candidates[: max(1, int(prefs.top_n))]


def recommend(*, data_parquet: Path, prefs: UserPrefs) -> list[dict[str, Any]]:
    df = pd.read_parquet(data_parquet)
    return recommend_from_df(df, prefs)

