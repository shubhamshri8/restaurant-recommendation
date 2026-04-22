from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from datasets import load_dataset


@dataclass(frozen=True)
class IngestionReport:
    dataset_name: str
    created_at: str
    rows_raw: int
    rows_written: int
    missing_city: int
    missing_name: int
    missing_rating: int
    missing_cost: int
    columns_in: list[str]
    columns_out: list[str]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_text(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    s = str(v).strip()
    return s if s else None


def _parse_float(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    s = _norm_text(v)
    if not s:
        return None
    s_cf = s.casefold()
    if s_cf in {"new", "nan", "n/a", "na", "-", "none"}:
        return None
    # Common Zomato formats: "4.1/5", "3.8 /5", "4.0/ 5"
    if "/" in s:
        s = s.split("/", 1)[0].strip()
    # Some datasets have trailing text, e.g. "4.1/5 (1000+)"
    s = s.replace("(", " ").split()[0].strip()
    try:
        return float(s)
    except Exception:
        return None


def _parse_int(v: Any) -> int | None:
    f = _parse_float(v)
    if f is None:
        return None
    try:
        return int(f)
    except Exception:
        return None


def _parse_cuisines(v: Any) -> list[str]:
    s = _norm_text(v)
    if not s:
        return []
    parts = [p.strip() for p in s.split(",")]
    cuisines = []
    for p in parts:
        if not p:
            continue
        # canonicalize lightly; keep original words/case mostly intact
        cuisines.append(" ".join(p.split()))
    # dedupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for c in cuisines:
        k = c.casefold()
        if k in seen:
            continue
        seen.add(k)
        out.append(c)
    return out


def _derive_budget_bucket(avg_cost_for_two_inr: float | None) -> str | None:
    if avg_cost_for_two_inr is None:
        return None
    # Simple INR buckets; tuned later from data quantiles if needed.
    if avg_cost_for_two_inr <= 700:
        return "low"
    if avg_cost_for_two_inr <= 1500:
        return "medium"
    return "high"


def ingest(
    *,
    output_parquet: Path,
    report_json: Path | None = None,
    dataset_name: str = "ManikaSaini/zomato-restaurant-recommendation",
) -> IngestionReport:
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    if report_json:
        report_json.parent.mkdir(parents=True, exist_ok=True)

    ds = load_dataset(dataset_name)
    # Use "train" if present; otherwise take first split.
    split_name = "train" if "train" in ds else list(ds.keys())[0]
    df = ds[split_name].to_pandas()
    columns_in = list(df.columns)
    rows_raw = len(df)

    # Heuristic column mapping across possible dataset variants
    col_name = next((c for c in df.columns if c.casefold() in {"restaurant name", "restaurant_name", "name"}), None)
    # This dataset is Bangalore-centric; it contains neighbourhoods/areas rather than true cities.
    # We normalize to: city="Bangalore" and area from "location" / "listed_in(city)".
    col_city = next((c for c in df.columns if c.casefold() in {"city"}), None)
    col_location = next((c for c in df.columns if c.casefold() in {"location"}), None)
    col_listed_city = next((c for c in df.columns if c.casefold() in {"listed_in(city)"}), None)
    col_area = next((c for c in df.columns if c.casefold() in {"area", "locality"}), None)
    col_cuisines = next((c for c in df.columns if c.casefold() in {"cuisines", "cuisine"}), None)
    col_rating = next((c for c in df.columns if c.casefold() in {"aggregate rating", "aggregate_rating", "rating", "rate"}), None)
    col_votes = next((c for c in df.columns if c.casefold() in {"votes", "vote"}), None)
    col_cost = next(
        (
            c
            for c in df.columns
            if c.casefold()
            in {
                "average cost for two",
                "average_cost_for_two",
                "avg_cost_for_two",
                "cost",
                "approx_cost(for two people)",
            }
        ),
        None,
    )
    col_currency = next((c for c in df.columns if c.casefold() in {"currency"}), None)

    out_rows: list[dict[str, Any]] = []
    missing_city = missing_name = missing_rating = missing_cost = 0

    for i, row in df.iterrows():
        name = _norm_text(row[col_name]) if col_name else None
        city_raw = _norm_text(row[col_city]) if col_city else None
        location_raw = _norm_text(row[col_location]) if col_location else None
        listed_area_raw = _norm_text(row[col_listed_city]) if col_listed_city else None
        area = _norm_text(row[col_area]) if col_area else None
        cuisines = _parse_cuisines(row[col_cuisines]) if col_cuisines else []
        rating = _parse_float(row[col_rating]) if col_rating else None
        votes = _parse_int(row[col_votes]) if col_votes else None

        cost = _parse_float(row[col_cost]) if col_cost else None
        # Currency is present in some datasets; this dataset is INR-centric, so we do not persist currency in Phase 1.
        _currency = _norm_text(row[col_currency]) if col_currency else None

        # Normalize location: attempt to extract city if locality_verbose-like values exist.
        city = city_raw
        # Prefer explicit locality/area if available; fall back to dataset area bucket.
        if area is None:
            area = location_raw or listed_area_raw

        # If dataset doesn't provide a true city, default to Bangalore.
        if not city:
            city = "Bangalore"

        if not name:
            missing_name += 1
        if not city:
            missing_city += 1
        if rating is None:
            missing_rating += 1
        if cost is None:
            missing_cost += 1

        # Skip rows without minimal identity fields
        if not name or not city or not cuisines or rating is None:
            continue

        avg_cost_for_two_inr = None
        if cost is not None:
            # Dataset is INR-centric for Zomato; if currency exists and isn't INR, still store numeric
            avg_cost_for_two_inr = float(cost)

        rest_id = f"rest_{i}"
        out_rows.append(
            {
                "id": rest_id,
                "name": name,
                "city": city,
                "area": area,
                "cuisines": cuisines,
                "avg_cost_for_two_inr": avg_cost_for_two_inr,
                "budget_bucket": _derive_budget_bucket(avg_cost_for_two_inr),
                "aggregate_rating": float(rating),
                "votes": votes,
                # Parquet cannot write an always-empty struct. Keep a stable field for future tag expansion.
                "tags": {"_reserved": None},
                "source": {
                    "dataset_name": dataset_name,
                    "dataset_version": None,
                    "raw_row_id": i,
                },
                "updated_at": _now_iso(),
            }
        )

    out_df = pd.DataFrame(out_rows)
    columns_out = list(out_df.columns)

    # Deduplicate loosely on (name, city, area) picking best rating then votes.
    if not out_df.empty:
        out_df["_area_key"] = out_df["area"].fillna("").astype(str).str.casefold()
        out_df["_name_key"] = out_df["name"].astype(str).str.casefold()
        out_df["_city_key"] = out_df["city"].astype(str).str.casefold()
        out_df["_votes_key"] = out_df["votes"].fillna(0)
        out_df = out_df.sort_values(["aggregate_rating", "_votes_key"], ascending=[False, False])
        out_df = out_df.drop_duplicates(subset=["_name_key", "_city_key", "_area_key"], keep="first")
        out_df = out_df.drop(columns=["_area_key", "_name_key", "_city_key", "_votes_key"])

    out_df.to_parquet(output_parquet, index=False)

    report = IngestionReport(
        dataset_name=dataset_name,
        created_at=_now_iso(),
        rows_raw=rows_raw,
        rows_written=len(out_df),
        missing_city=missing_city,
        missing_name=missing_name,
        missing_rating=missing_rating,
        missing_cost=missing_cost,
        columns_in=columns_in,
        columns_out=columns_out,
    )
    if report_json:
        report_json.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
    return report


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Ingest Zomato dataset and write normalized parquet.")
    parser.add_argument("--out", default="data/restaurants.parquet", help="Output parquet path")
    parser.add_argument("--report", default="data/ingestion_report.json", help="Optional ingestion report JSON path")
    args = parser.parse_args()

    report = ingest(output_parquet=Path(args.out), report_json=Path(args.report))
    print(json.dumps(asdict(report), indent=2))


if __name__ == "__main__":
    main()

