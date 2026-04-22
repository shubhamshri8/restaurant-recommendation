from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

try:
    from src.phase1.retrieval.recommend import UserPrefs, recommend
except ModuleNotFoundError:
    # Allows: `python3 src/phase1/cli.py ...` without requiring PYTHONPATH.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.phase1.retrieval.recommend import UserPrefs, recommend


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Offline restaurant recommendations (Phase 1).")
    p.add_argument("--data", default="data/restaurants.parquet", help="Path to normalized restaurants parquet")
    p.add_argument("--area", required=True, help="Bangalore area/locality (Phase 1 dataset is Bangalore-only)")
    p.add_argument("--budget-inr", type=float, required=True, help="Approx budget for two (INR)")
    p.add_argument("--cuisine", required=True, help="Cuisine (exact match, case-insensitive)")
    p.add_argument("--min-rating", type=float, default=0.0, help="Minimum rating (0-5)")
    p.add_argument("--notes", default=None, help="Optional free-text preferences (unused in Phase 1)")
    p.add_argument("--top-n", type=int, default=5, help="Number of results to return")
    p.add_argument("--json", action="store_true", help="Print as JSON")
    args = p.parse_args()

    prefs = UserPrefs(
        area=args.area,
        budget_inr=float(args.budget_inr),
        cuisine=args.cuisine,
        min_rating=float(args.min_rating),
        notes=args.notes,
        top_n=int(args.top_n),
    )

    results = recommend(data_parquet=Path(args.data), prefs=prefs)
    if args.json:
        print(json.dumps({"request": asdict(prefs), "results": results}, indent=2))
    else:
        if not results:
            print("No matches found. Try lowering min rating, widening budget, or changing cuisine/location.")
            return
        for i, r in enumerate(results, start=1):
            print(f"{i}. {r['name']}  |  {', '.join(r['cuisines'])}  |  ⭐ {r['rating']:.1f}  |  Cost: {r['estimated_cost']}")
            print(f"   {r['reason']}")


if __name__ == "__main__":
    main()

