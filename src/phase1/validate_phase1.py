from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def _load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def validate_contract_examples() -> None:
    prefs_schema = _load_json(ROOT / "contracts/schemas/user-prefs.schema.json")
    resp_schema = _load_json(ROOT / "contracts/schemas/recommendations-response.schema.json")

    prefs_example = _load_json(ROOT / "contracts/examples/user-prefs.sample.json")
    resp_example = _load_json(ROOT / "contracts/examples/recommendations-response.sample.json")

    jsonschema.validate(instance=prefs_example, schema=prefs_schema)
    jsonschema.validate(instance=resp_example, schema=resp_schema)


def validate_parquet(path: Path) -> None:
    df = pd.read_parquet(path)
    required_cols = {
        "id",
        "name",
        "city",
        "area",
        "cuisines",
        "avg_cost_for_two_inr",
        "aggregate_rating",
        "votes",
        "updated_at",
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise SystemExit(f"Parquet missing required columns: {sorted(missing)}")

    if len(df) == 0:
        raise SystemExit("Parquet contains 0 rows.")


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Validate Phase 0 contracts and Phase 1 data artifact.")
    p.add_argument("--data", default="data/restaurants.parquet", help="Path to parquet to validate")
    args = p.parse_args()

    validate_contract_examples()
    validate_parquet(Path(args.data))
    print("OK: contracts examples validate; parquet looks sane.")


if __name__ == "__main__":
    main()

