from __future__ import annotations

import json
import logging
from typing import Any

from src.phase2.llm.client import LlmConfig, chat_json
from src.phase2.llm.prompt import (
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_STRICT,
    build_retry_user_prompt,
    build_user_prompt,
)
from src.phase1.retrieval.recommend import UserPrefs

logger = logging.getLogger(__name__)


def _extract_json_array(text: str) -> list[dict[str, Any]]:
    """
    Best-effort extraction of a top-level JSON array from model output.
    We instruct strict JSON, but keep this robust for safety.
    """
    s = text.strip()
    if s.startswith("["):
        parsed = json.loads(s)
    else:
        start = s.find("[")
        end = s.rfind("]")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Model output did not contain a JSON array.")
        parsed = json.loads(s[start : end + 1])
    if not isinstance(parsed, list):
        raise ValueError("Model output JSON is not an array.")
    return parsed


def _normalize_match_signals(raw: Any) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for x in raw:
        if isinstance(x, str) and x.strip():
            out.append(x.strip())
    return out


def _strip_for_llm(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Do not pass heuristic reason/_score to the model."""
    clean: list[dict[str, Any]] = []
    for c in candidates:
        d = {k: v for k, v in c.items() if k not in {"reason", "_score"}}
        clean.append(d)
    return clean


def _merge_llm_row(
    *,
    item: dict[str, Any],
    allowed_ids: set[str],
    id_to_candidate: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    rid = item.get("restaurant_id")
    if not isinstance(rid, str) or rid not in allowed_ids:
        return None
    reason = item.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        return None
    base = id_to_candidate[rid]
    return {
        "restaurant_id": rid,
        "name": base["name"],
        "cuisines": base["cuisines"],
        "rating": base["rating"],
        "estimated_cost": base["estimated_cost"],
        "reason": reason.strip(),
        "match_signals": _normalize_match_signals(item.get("match_signals")),
    }


def _parse_llm_output(
    raw: str,
    *,
    candidates: list[dict[str, Any]],
    prefs: UserPrefs,
) -> list[dict[str, Any]]:
    parsed = _extract_json_array(raw)
    allowed_ids = {c["restaurant_id"] for c in candidates}
    id_to_candidate = {c["restaurant_id"]: c for c in candidates}

    out: list[dict[str, Any]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        merged = _merge_llm_row(item=item, allowed_ids=allowed_ids, id_to_candidate=id_to_candidate)
        if merged is None:
            continue
        out.append(merged)
        if len(out) >= int(prefs.top_n):
            break

    if not out:
        raise ValueError("LLM rerank produced no valid results.")
    return out


def rerank_with_llm(
    *,
    prefs: UserPrefs,
    candidates: list[dict[str, Any]],
    config: LlmConfig,
) -> tuple[list[dict[str, Any]], dict]:
    clean = _strip_for_llm(candidates)
    user_prompt = build_user_prompt(prefs=prefs, candidates=clean)

    try:
        raw, usage = chat_json(system=SYSTEM_PROMPT, user=user_prompt, config=config)
        return _parse_llm_output(raw, candidates=candidates, prefs=prefs), usage
    except Exception as e:
        logger.warning("LLM rerank first attempt failed: %s", e)

    # Retry once with stricter system prompt + explicit repair instruction.
    retry_user = build_retry_user_prompt(prefs=prefs, candidates=clean)
    raw2, usage2 = chat_json(system=SYSTEM_PROMPT_STRICT, user=retry_user, config=config)
    return _parse_llm_output(raw2, candidates=candidates, prefs=prefs), usage2
