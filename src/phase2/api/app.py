from __future__ import annotations

import logging
import os
import uuid
import time
from pathlib import Path

import pandas as pd
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.phase2.api.response_builder import build_response, deterministic_results
from src.phase2.api.validation import ensure_data_exists
from src.phase2.llm.client import load_llm_config
from src.phase2.llm.rerank import rerank_with_llm
from src.phase1.retrieval.recommend import UserPrefs, shortlist_from_df

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_PATH = Path(os.getenv("RESTAURANTS_DATA_PATH", "data/restaurants.parquet"))
_k = int(os.getenv("LLM_SHORTLIST_K", "50"))
SHORTLIST_K = max(30, min(60, _k))

app = FastAPI(
    title="Restaurant Recommendations API",
    version="0.3.0",
    description="Phase 2 LLM rerank with parquet retrieval.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendRequest(BaseModel):
    area: str = Field(min_length=1, description="Bangalore area/locality")
    budget_inr: float = Field(ge=0, description="Approx budget for two (INR)")
    cuisine: str = Field(min_length=1)
    min_rating: float = Field(ge=0, le=5, default=0)
    notes: str | None = None
    top_n: int = Field(ge=1, le=20, default=20)


_df_cache: pd.DataFrame | None = None


def _get_df() -> pd.DataFrame:
    global _df_cache
    ensure_data_exists(DATA_PATH.exists())
    if _df_cache is None:
        _df_cache = pd.read_parquet(DATA_PATH)
    return _df_cache


@app.get("/health")
def health():
    return {"ok": True, "storage": "parquet"}


@app.get("/explore")
def explore(limit: int = 6, cuisine: str | None = None):
    request_id = f"explore_{uuid.uuid4().hex[:8]}"
    df = _get_df()
    
    # Filter by cuisine if provided
    working_df = df
    if cuisine:
        target = cuisine.lower()
        def matches(c_data):
            if c_data is None:
                return False
            # Handle both list/ndarray and string (fallback)
            if isinstance(c_data, (list, np.ndarray)):
                return any(target in str(c).lower() for c in c_data)
            return target in str(c_data).lower()
            
        mask = working_df['cuisines'].apply(matches)
        if mask.any():
            working_df = working_df[mask]
    
    # Get top rated restaurants
    top_df = working_df.sort_values(by=['aggregate_rating', 'votes'], ascending=[False, False]).head(limit)
    
    results = []
    for _, row in top_df.iterrows():
        cuisines_str = row.get('cuisines', [])
        # Handle both list and string
        if isinstance(cuisines_str, (list, np.ndarray)):
            cuisines_list = [str(c).strip() for c in cuisines_str if str(c).strip()]
        else:
            cuisines_list = [c.strip() for c in str(cuisines_str).split(',') if c.strip()]
        
        reason = f"One of the top-rated {cuisine} restaurants." if cuisine else "Top rated restaurant in the city. Highly recommended for a premium experience."
        rating_val = row.get('aggregate_rating', 0.0)
        cost_val = row.get('avg_cost_for_two_inr', 0)
        
        results.append({
            "restaurant_id": str(row.get('id', '')),
            "name": str(row.get('name', '')),
            "cuisines": cuisines_list,
            "rating": float(rating_val) if not pd.isna(rating_val) else 0.0,
            "estimated_cost": int(float(cost_val)) if not pd.isna(cost_val) else 0,
            "reason": reason,
            "match_signals": [f"{cuisine} Specialty", "Highly Rated"] if cuisine else ["Exceptional Rating", "City Favorite"]
        })
        
    return build_response(request_id=request_id, results=results)


@app.post("/recommendations")
def recommendations(req: RecommendRequest):
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    prefs = UserPrefs(
        area=req.area,
        budget_inr=req.budget_inr,
        cuisine=req.cuisine,
        min_rating=req.min_rating,
        notes=req.notes,
        top_n=req.top_n,
    )

    t0 = time.time()
    df = _get_df()
    shortlist = shortlist_from_df(df, prefs, k=SHORTLIST_K)
    retrieval_latency = time.time() - t0

    usage = {"prompt_tokens": 0, "completion_tokens": 0}
    llm_latency = 0.0

    if not shortlist:
        logger.info(
            "Request %s | Area: %s | Cuisine: %s | Shortlist: 0 | RetLatency: %.3fs",
            request_id, req.area, req.cuisine, retrieval_latency
        )
        return build_response(request_id=request_id, results=[])

    llm_config = load_llm_config()
    if llm_config:
        try:
            t1 = time.time()
            results, usage = rerank_with_llm(prefs=prefs, candidates=shortlist, config=llm_config)
            llm_latency = time.time() - t1
            
            logger.info(
                "Request %s | Area: %s | Cuisine: %s | Shortlist: %d | RetLatency: %.3fs | LLMLatency: %.3fs | PT: %d | CT: %d",
                request_id, req.area, req.cuisine, len(shortlist), retrieval_latency, llm_latency,
                usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
            )
            return build_response(request_id=request_id, results=results)
        except Exception as e:
            logger.warning("LLM rerank failed; using deterministic fallback: %s", e)

    results = deterministic_results(df, prefs)
    logger.info(
        "Request %s | Area: %s | Cuisine: %s | Shortlist: %d | RetLatency: %.3fs | Fallback",
        request_id, req.area, req.cuisine, len(shortlist), retrieval_latency
    )
    return build_response(request_id=request_id, results=results)

