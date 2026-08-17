"""
Composio Toolkit Radar – FastAPI Backend
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
import json
import os
from datetime import datetime, timezone

from backend.schemas import AppResearch
from backend.workflow.graph import run_research_pipeline
from backend.db.sqlite import init_db, save_app_research, get_app_research

app = FastAPI(title="Composio Toolkit Radar", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def load_json(filename: str) -> Any:
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_json(filename: str, data: Any):
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


# ── Endpoints ──

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/apps")
def get_apps():
    return load_json("apps.json")


@app.get("/results")
def get_results():
    return load_json("results.json")


@app.get("/results/{app_name}")
def get_result(app_name: str):
    results = load_json("results.json")
    for r in results:
        if r.get("app_name", "").lower() == app_name.lower():
            return r
    cached = get_app_research(app_name)
    if cached:
        return cached
    raise HTTPException(status_code=404, detail="Result not found")


@app.post("/research/{app_name}")
async def research_app(app_name: str):
    apps = load_json("apps.json")
    target = next(
        (a for a in apps if a["app_name"].lower() == app_name.lower()),
        {"app_name": app_name, "category": "Unknown", "website": ""},
    )

    result = await run_research_pipeline(
        app_name=target["app_name"],
        category=target["category"],
        website=target["website"],
    )

    data = result.model_dump()
    save_app_research(app_name, data)
    return data


@app.get("/verification")
def get_verification():
    return load_json("verification.json")


@app.get("/recommendations")
def get_recommendations():
    results = load_json("results.json")
    recs = []
    for r in results:
        rec = r.get("recommendation", {})
        comp = r.get("composio", {})
        if rec.get("buildability") == "GREEN" and comp.get("currently_supported") in ("no", "fuzzy_match"):
            recs.append(r)
    recs.sort(key=lambda x: x.get("recommendation", {}).get("score", 0), reverse=True)
    return recs


@app.get("/summary")
def get_summary():
    return load_json("summary.json")
