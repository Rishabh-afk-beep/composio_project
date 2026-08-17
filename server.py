import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Ensure backend package can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.workflow.graph import run_research_pipeline
from backend.schemas import AppResearch

app = FastAPI(title="Composio Toolkit Radar API")

# Allow frontend to call the API
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
allow_origins = [frontend_url] if frontend_url != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/research/{app_name}")
async def research_app_endpoint(app_name: str):
    """
    Kicks off the full agentic pipeline to research a single application.
    Returns the structured findings and build priority.
    """
    print(f"\n[API] Received request to research: {app_name}")
    try:
        # Run the LangGraph/Agent pipeline
        # Pass dummy strings for category and website since frontend doesn't provide them
        result: AppResearch = await run_research_pipeline(app_name, "Unknown", "unknown.com")
        return result.model_dump()
    except Exception as e:
        print(f"[API] Error researching {app_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting API Server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
