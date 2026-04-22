# Restaurant Recommendation (Phase-wise build)

This project implements an AI-powered restaurant recommendation system (Zomato-inspired). See `docs/problemStatement.md` and `docs/architecture-phases.md`.

## Phase 0

- `contracts/`: JSON Schemas + sample payloads
- `data/`: generated artifacts (gitignored)

## Phase 1

1. Create a venv and install deps: `pip install -r requirements.txt`
2. Ingest: `python3 src/phase1/ingestion/ingest.py`
3. CLI: `python3 src/phase1/cli.py --area Indiranagar --budget-inr 1500 --cuisine Italian --min-rating 4.0`

## Phase 2 (LLM rerank + API)

**Environment**

- `GROQ_API_KEY`: required for LLM rerank (if unset, API falls back to Phase 1 deterministic ranking).
- Optional: `GROQ_MODEL` (default `llama-3.1-8b-instant`), `GROQ_TIMEOUT_S`, `GROQ_MAX_RETRIES`, `RESTAURANTS_DATA_PATH`, `LLM_SHORTLIST_K` (30–60).

**Run API**

```bash
. .venv/bin/activate
uvicorn src.phase2.api.app:app --reload --host 0.0.0.0 --port 8000
```

- `GET /health`
- `POST /recommendations` with JSON body matching `contracts/schemas/user-prefs.schema.json` (`area`, `budget_inr`, `cuisine`, `min_rating`, optional `notes`, `top_n`).

Flow: deterministic shortlist → LLM returns ranked `restaurant_id` + `reason` (+ optional `match_signals`) → validated against candidates; on failure, deterministic results.

## Phase 3 (Postgres + hybrid notes retrieval)

**When `DATABASE_URL` is set**, the API uses **Postgres** for retrieval (indexes on city, area, rating, cuisines GIN, cost). If it is **unset**, behavior matches Phase 2 using **`data/restaurants.parquet`**.

**Setup**

1. Run Postgres and create the schema:

   ```bash
   psql "$DATABASE_URL" -f db/schema.sql
   ```

2. Load data from Phase 1 parquet (optional embeddings for hybrid `notes`):

   ```bash
   export DATABASE_URL="postgresql://USER:PASS@localhost:5432/DBNAME"
   # Embeddings use OPENAI_EMBEDDING_MODEL (default text-embedding-3-small) when OPENAI_API_KEY is set
   python3 -m src.phase3.db.loader --parquet data/restaurants.parquet
   ```

**Hybrid behavior**

- **Hard filters** (area, min rating, budget band, cuisine) match `docs/architecture-phases.md`.
- If **`notes`** is non-empty and **query + row embeddings** exist, shortlist order blends **embedding similarity** with the heuristic score; otherwise heuristic only.

**Keys**

- **Required for DB path**: `DATABASE_URL`
- **Optional for embeddings at load time / query**: `OPENAI_API_KEY` (note: Phase 3 embeddings still use OpenAI)
- Optional: `OPENAI_EMBEDDING_MODEL` (default `text-embedding-3-small`)

`GET /health` reports `storage: postgres` and `db_ok` when the database is configured and reachable.
