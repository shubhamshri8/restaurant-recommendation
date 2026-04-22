# Phase-wise Architecture — AI-Powered Restaurant Recommendation (Zomato use case)

This document breaks the system into phases so you can build iteratively while keeping a clear path to a production-grade architecture.

---

## Assumptions (explicit)

- **Dataset**: Hugging Face `ManikaSaini/zomato-restaurant-recommendation` (loaded offline, refreshed on demand).
- **Primary user inputs**: `area` (Bangalore locality), `budget_inr` (numeric), `cuisine`, `min_rating`, `notes` (free text).
- **Output**: top N restaurants with structured fields plus an LLM-generated explanation.
- **LLM usage**: used only on a **shortlisted candidate set**, never on the full dataset. (Using Groq as the primary LLM provider, with the API key managed via `.env` file).
- **Storage**: Local Parquet files (`data/restaurants.parquet`) used for high-performance retrieval without a database.

---

## Shared domain contracts (all phases)

### Restaurant entity (normalized)

- **id**: stable identifier (generated if not present)
- **name**: string
- **location**:
  - `city`: string (e.g., "Delhi")
  - `area`: optional string (if available)
  - `lat`, `lng`: optional floats (if available)
- **cuisines**: string[] (canonicalized)
- **cost**:
  - `avg_cost_for_two_inr`: number (if available; normalized to INR)
  - `budget_bucket`: enum `"low" | "medium" | "high"` (derived; used internally for coarse filtering)
- **rating**:
  - `aggregate_rating`: number (0–5)
  - `votes`: optional number
- **attributes/tags** (derived where possible):
  - `family_friendly`, `quick_service`: optional booleans
- **source**:
  - `dataset_name`, `dataset_version`, `raw_row_id`
- **updated_at**: timestamp

### User preference contract

- **area**: string (Bangalore locality; dataset scope is Bangalore)
- **budget_inr**: number (interpreted as an approximate "cost for two" budget in INR)
- **cuisine**: string (single) or string[] (optional extension)
- **min_rating**: number (0–5)
- **notes**: string (optional)

### Recommendation output contract

- **request_id**: string
- **results**: array of:
  - `restaurant_id`
  - `name`
  - `cuisines`
  - `rating`
  - `estimated_cost`
  - `reason` (LLM explanation in phases with LLM; deterministic explanation in earlier phases)
  - `match_signals` (optional, machine-readable reasons)

---

## Phase 0 — Foundation [COMPLETED]

### Goal
Freeze the system contracts early (entities, inputs, outputs) to keep later changes non-breaking.

### Components
- **Schema module**: Defines `Restaurant`, `UserPrefs`, `RecommendationResult`.
- **Config module**: Dataset source location (HF name), local artifact paths.
- **Repo structure**:
  - `docs/architecture-phases.md` (this file)
  - `data/` (parquet artifacts, ingestion reports)
  - `src/phase1/` — ingestion, core retrieval, CLI
  - `src/phase2/` — LLM + HTTP API (FastAPI)
  - `src/phase3/` — Evaluation scripts
  - `frontend/` — React/Vite/Tailwind UI

---

## Phase 1 — Offline MVP (no LLM) [COMPLETED]

### Goal
End-to-end recommendations without LLM: ingestion → filter/rank → display.

### Components
- **Ingestion job**: `src/phase1/ingestion/ingest.py`
  - Normalizes HF dataset to `data/restaurants.parquet`.
  - Handles canonicalization, budget bucketing, and deduplication.
- **Retrieval module**: `src/phase1/retrieval/recommend.py`
  - Filter logic for area, rating, cuisine, and budget band.
  - Scoring heuristic: `0.70 * rating + 0.20 * cost_proximity + 0.10 * votes`.
- **CLI interface**: `src/phase1/cli.py` for testing retrieval without an API.

---

## Phase 2 — LLM MVP: rerank + explanations [COMPLETED]

### Goal
Add human-like ranking and explanations using Groq LLM on a curated candidate set.

### Components
- **API service**: `src/phase2/api/app.py` (FastAPI)
  - `POST /recommendations`: Main endpoint with LLM reranking and deterministic fallback.
  - `GET /explore`: New endpoint for discoverability (top-rated restaurants by cuisine).
  - `GET /health`: Health checks and storage status.
- **LLM Engine**: `src/phase2/llm/`
  - `rerank.py`: Orchestrates the Groq LLM call with a shortlisted candidate set (K=30-60).
  - `prompt.py`: Manages system instructions and JSON output enforcement.
- **Validation**: Strict JSON schema validation for LLM responses to prevent hallucinations.

---

## Phase 3 — Quality + evaluation loop [COMPLETED]

### Goal
Make results reliable, measurable, and safe to iterate on.

### Implementation
- **Evaluation Harness**: `src/phase3/evaluate.py`
  - Uses `TestClient` to run a suite of test queries against the live API.
  - Checks for constraint violations (e.g., rating lower than requested) and presence of LLM explanations.
  - Reports average latency and pass rates.
- **Observability**:
  - Structured logging in `app.py` tracking retrieval vs. LLM latency.
  - Token usage tracking (prompt vs. completion) for cost monitoring.

---

## Phase 4 — UX Polish + Scaling [IN PROGRESS]

### Goal
Transition to a premium web product with production-grade reliability.

### Components
- **Frontend (Advanced)**:
  - Editorial-grade light theme with cuisine galleries and sticky refinement bars.
  - Responsive layout for mobile and desktop.
- **Scaling concerns**:
  - Caching deterministic retrieval results.
  - Caching LLM responses keyed by preference hash.
  - Containerization (Docker) for consistent deployment.

---

## Appendix — API Reference

### `POST /recommendations`
Request: `area, budget_inr, cuisine, min_rating, notes?, top_n?`
Response: `request_id, results: [{restaurant_id, name, cuisines, rating, estimated_cost, reason, match_signals}]`

### `GET /explore`
Query Params: `limit? (default 6), cuisine?`
Returns top-rated restaurants to help users discover the platform.

### `GET /health`
Returns system status and storage backend (Parquet).

