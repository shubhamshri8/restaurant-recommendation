# `src/` layout

Code is grouped **by phase** (see `docs/architecture-phases.md`).

| Folder | Contents |
|--------|----------|
| `phase1/` | Ingestion, core retrieval (`recommend.py`), CLI, Phase 1 validation |
| `phase2/` | LLM client/prompt/rerank, FastAPI (`POST /recommendations`) |
| `phase3/` | Postgres (`db/`), DB-backed + hybrid shortlist (`retrieval/db_shortlist.py`) |

**Run from repository root** (so `python3 -m` and `src.*` imports resolve).

Examples:

- Ingest: `python3 src/phase1/ingestion/ingest.py`
- CLI: `python3 src/phase1/cli.py --area …`
- API: `uvicorn src.phase2.api.app:app --reload`
- DB load: `python3 -m src.phase3.db.loader`
