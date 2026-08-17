# Composio Toolkit Radar

Automated AI-driven research pipeline for evaluating API integration readiness across SaaS applications to prioritize the Composio toolkit roadmap.

## Architecture

This project is divided into two parts:
1. **Python Agentic Backend (FastAPI)**: An orchestration of autonomous agents (Planner, Firecrawl Researcher, Gemini LLM Extractors, Verifier, Scorer) that navigate the web, read developer docs, and extract highly structured integration readiness metadata (API type, Authentication model, MCP presence).
2. **Vanilla JS Frontend**: A dashboard presenting the matrix of findings, key patterns, and verification metrics. It allows you to invoke the backend live to research an app in real-time.

### How the Pipeline Works
1. **Planner**: Creates strategic search queries using the app's domain.
2. **Firecrawl Extraction**: Scrapes deep developer documentation from the web.
3. **Parallel LLM Researchers**: Gemini 1.5 processes the context to extract API breadth, Auth methods, and Model Context Protocol (MCP) status into strict Pydantic schemas.
4. **Verification**: A strict verification agent checks the claims against evidence. If unsupported, the confidence score drops to zero.
5. **Deterministic Scoring**: An algorithmic function assigns a build priority (e.g., P0, P1, RED) based on self-serve access, API availability, and documentation quality.

## Local Setup

### Prerequisites
- Python 3.10+
- `pip`

### Installation
1. Clone the repository.
2. Install Python dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure your API keys.

### Running Locally
1. Start the FastAPI backend:
   ```bash
   uvicorn server:app --host 0.0.0.0 --port 8000
   ```
2. Start the frontend locally (e.g., using Python's http.server):
   ```bash
   python -m http.server 3000 --directory frontend
   ```
3. Open `http://localhost:3000` in your browser.

## Environment Variables
The backend requires the following keys in your `.env` (local) or your Render environment dashboard (production):
- `GEMINI_API_KEY`: Google Gemini API Key.
- `FIRECRAWL_API_KEY`: Firecrawl API Key for web scraping.
- `COMPOSIO_API_KEY`: (Optional) For checking live toolkit coverage.
- `FRONTEND_URL`: (Production only) The URL of the deployed Vercel frontend, used to configure CORS securely.

The frontend requires:
- `API_URL`: (Production only, configured in Vercel) The URL of the deployed Render backend.

## Deployment Architecture
- **Backend**: Deployed on Render using the included `render.yaml` specification.
- **Frontend**: Deployed on Vercel as a static site. A build script in `package.json` dynamically injects the `API_URL` environment variable during the Vercel build phase.

## Live Demo URLs
- **Frontend**: [Your Vercel URL]
- **Backend API**: [Your Render URL]

## Known Limitations & Testing Notes
- **Gemini Quota Exhaustion**: We built a highly robust error-handling system because the free tier of the Gemini API hits its daily quota quickly when processing multi-agent pipelines. 
- **Controlled Pilot**: Due to the API quota limit, we ran a heavily controlled sequential test on 5 apps (Supabase, Salesforce, Slack, Stripe, Notion). The pipeline safely executes, detects the `429 RESOURCE_EXHAUSTED` error, prevents hallucinations, skips verification, explicitly sets the confidence to 0, and records the error state. 
- *Note: The system is designed to run 100 apps asynchronously, but we explicitly halted the 100-app batch to prevent fabricated results until a paid tier API key is provided.*
