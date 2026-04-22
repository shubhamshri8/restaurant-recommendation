from __future__ import annotations

import json
from dataclasses import asdict

from src.phase1.retrieval.recommend import UserPrefs


SYSTEM_PROMPT = """You are a restaurant recommendation assistant.
You will be given:
1) User preferences
2) A list of candidate restaurants (the only allowed restaurants)

Rules:
- ONLY recommend restaurants from the candidates list.
- Do NOT invent restaurants or attributes not present in the candidate data.
- Return STRICT JSON only, no markdown, no extra text.

Output format:
[
  {
    "restaurant_id": "string (must match a candidate id)",
    "reason": "1-2 concise sentences explaining the match",
    "match_signals": ["optional", "string", "signals"]
  }
]

Order the array by best match first. Include at most top_n items."""

SYSTEM_PROMPT_STRICT = SYSTEM_PROMPT + """

Additional constraints for this attempt:
- Every restaurant_id MUST appear exactly as in candidates.
- match_signals must be an array of short strings (or omit if empty).
- Do not mention prices or ratings that are not in the candidate objects."""

RETRY_USER_SUFFIX = (
    "\n\nYour previous response was invalid or incomplete. "
    "Reply again with ONLY a JSON array, no prose, "
    "using only restaurant_id values from candidates, ordered best-first."
)


def _compact_candidates_for_llm(candidates: list[dict]) -> list[dict]:
    out: list[dict] = []
    for c in candidates:
        cuisines = c["cuisines"]
        if not isinstance(cuisines, list):
            cuisines = list(cuisines)
        out.append(
            {
                "restaurant_id": c["restaurant_id"],
                "name": c["name"],
                "area": c.get("area"),
                "cuisines": cuisines,
                "rating": c["rating"],
                "estimated_cost": c["estimated_cost"],
            }
        )
    return out


def build_user_prompt(*, prefs: UserPrefs, candidates: list[dict]) -> str:
    compact_candidates = _compact_candidates_for_llm(candidates)
    prefs_payload = asdict(prefs)
    return json.dumps(
        {
            "scope": "Bangalore only (area/locality within Bangalore).",
            "preferences": prefs_payload,
            "candidates": compact_candidates,
            "instructions": {
                "top_n": prefs.top_n,
                "ranking_goal": "Return the best matches, prioritizing rating and budget fit, then explain clearly.",
            },
        },
        ensure_ascii=False,
    )


def build_retry_user_prompt(*, prefs: UserPrefs, candidates: list[dict]) -> str:
    return build_user_prompt(prefs=prefs, candidates=candidates) + RETRY_USER_SUFFIX
