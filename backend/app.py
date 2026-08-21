from __future__ import annotations
import os
from dotenv import load_dotenv

# Load environment variables from the .env file BEFORE starting the app
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.analysis import router as analysis_router


app = FastAPI(
    title="AI-Powered Software Quality Platform",
    version="1.0.0",
    description="Code analysis, defect prediction, test intelligence, bug reporting, semantic search, and Gemini-powered developer assistance.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}