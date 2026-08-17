"""
Research a single app from the command line.

Usage:
  python scripts/research_one.py --app "Podio"
"""
import argparse
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.workflow.graph import run_research_pipeline
from backend.db.sqlite import init_db


async def main():
    parser = argparse.ArgumentParser(description="Research a single app")
    parser.add_argument("--app", required=True, help="App name to research")
    args = parser.parse_args()

    init_db()

    # Load apps list to find category/website
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    apps_path = os.path.join(data_dir, "apps.json")
    apps = []
    if os.path.exists(apps_path):
        with open(apps_path, "r") as f:
            apps = json.load(f)

    target = next(
        (a for a in apps if a["app_name"].lower() == args.app.lower()),
        {"app_name": args.app, "category": "Unknown", "website": ""},
    )

    print(f"\n{'='*60}")
    print(f"  Composio Toolkit Radar – Researching: {target['app_name']}")
    print(f"{'='*60}\n")

    result = await run_research_pipeline(
        app_name=target["app_name"],
        category=target["category"],
        website=target["website"],
    )

    output = result.model_dump()
    print(f"\n{'='*60}")
    print(json.dumps(output, indent=2, default=str))

    # Also save to results.json (merge)
    results_path = os.path.join(data_dir, "results.json")
    results = []
    if os.path.exists(results_path):
        with open(results_path, "r") as f:
            results = json.load(f)

    # Replace or append
    replaced = False
    for i, r in enumerate(results):
        if r.get("app_name", "").lower() == target["app_name"].lower():
            results[i] = output
            replaced = True
            break
    if not replaced:
        results.append(output)

    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n> Saved to {results_path}")


if __name__ == "__main__":
    asyncio.run(main())
