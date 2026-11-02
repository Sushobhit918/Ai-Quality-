from __future__ import annotations
from dotenv import load_dotenv

# Load local environment variables before importing application services.
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.analysis import router as analysis_router


app = FastAPI(
    title="AI-Powered Software Quality Platform",
    version="1.0.0",
    description="Code analysis, defect prediction, test intelligence, bug reporting, semantic search, and Gemini-powered developer assistance.",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# The frontend and API share one Vercel origin. CORS remains enabled for
# local development and any explicitly configured external clients.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel's service rewrite preserves the incoming /api prefix.
app.include_router(analysis_router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
