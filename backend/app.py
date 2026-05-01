"""
backend/app.py

FastAPI backend for the Bluesky Post Explainer.

Endpoints:
- GET  /health
- POST /explain

In production Docker, this also serves the React frontend from frontend/dist.
"""

import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent.orchestrator import explain_bluesky_url


### ---------------------------------------------------------------------------
### Environment
### ---------------------------------------------------------------------------

load_dotenv()


### ---------------------------------------------------------------------------
### FastAPI app
### ---------------------------------------------------------------------------

app = FastAPI(
    title="Bluesky Post Explainer API",
    version="1.0.0",
)


### ---------------------------------------------------------------------------
### CORS
### ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


### ---------------------------------------------------------------------------
### Schemas
### ---------------------------------------------------------------------------

class ExplainRequest(BaseModel):
    """
    Request body for /explain.
    """

    url: str = Field(..., description="Bluesky post URL")
    analyze_images: bool = True
    reanalyze_with_images: bool = False


class ExplainResponse(BaseModel):
    """
    Flexible response model because the agent returns nested metadata.
    """

    post: Dict[str, Any]
    analysis: Dict[str, Any]
    image_insights: list
    image_context: str
    retrieval_context: str
    explanation: str


### ---------------------------------------------------------------------------
### API routes
### ---------------------------------------------------------------------------

@app.get("/health")
def health() -> Dict[str, str]:
    """
    Health check endpoint.
    """

    return {"status": "ok"}


@app.post("/explain", response_model=ExplainResponse)
def explain(request: ExplainRequest) -> Dict[str, Any]:
    """
    Explain a Bluesky post URL.
    """

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not configured.",
        )

    try:
        return explain_bluesky_url(
            url=request.url,
            analyze_images=request.analyze_images,
            reanalyze_with_images=request.reanalyze_with_images,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to explain post: {exc}",
        ) from exc


### ---------------------------------------------------------------------------
### Static React frontend
### ---------------------------------------------------------------------------

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIST), html=True),
        name="frontend",
    )