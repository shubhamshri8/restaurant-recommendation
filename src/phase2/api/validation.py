from __future__ import annotations

from fastapi import HTTPException


def ensure_data_exists(path_exists: bool) -> None:
    if not path_exists:
        raise HTTPException(
            status_code=400,
            detail="Data file missing. Run Phase 1 ingestion: python3 src/ingestion/ingest.py",
        )
