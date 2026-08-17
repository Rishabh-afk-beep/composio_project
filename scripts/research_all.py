"""
Research all 100 apps in batch. Saves incrementally to data/results.json.

Usage:
  python scripts/research_all.py
  python scripts/research_all.py --start 10 --end 20   # subset
"""
import argparse
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.workflow.graph import run_research_pipeline
from backend.db.sqlite import init_db

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def load_json(name):
    p = os.path.join(DATA_DIR, name)
    if os.path.exists(p):
        with open(p, "r") as f:
            return json.load(f)
    return []


def save_json(name, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, name), "w") as f:
        json.dump(data, f, indent=2, default=str)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    args = parser.parse_args()

    init_db()
    apps = load_json("apps.json")
    subset = apps[args.start:args.end]

    results = load_json("results.json")
    if not isinstance(results, list):
        results = []
    completed = {r["app_name"]: r for r in results if r}

    total = len(subset)
    print(f"\n{'='*60}")
    print(f"  Composio Toolkit Radar – Batch Research")
    print(f"  {total} apps to process, {len(completed)} already cached")
    print(f"{'='*60}\n")

    succeeded, failed = 0, 0
    for i, app in enumerate(subset):
        name = app["app_name"]
        if name in completed:
            print(f"[{i+1}/{total}] ⏩ Skipping {name} (cached)")
            continue

        print(f"\n[{i+1}/{total}] Researching {name}...")
        try:
            result = await run_research_pipeline(
                app_name=name,
                category=app["category"],
                website=app["website"],
            )
            completed[name] = result.model_dump()
            save_json("results.json", list(completed.values()))
            succeeded += 1
        except Exception as e:
            print(f"  ✗ FAILED: {name}: {e}")
            failed += 1

        await asyncio.sleep(2)  # rate-limit between apps

    print(f"\n{'='*60}")
    print(f"  Done. {succeeded} succeeded, {failed} failed, {len(completed)} total cached.")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
