from typing import Any, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    project_path: str = Field(..., description="Absolute or workspace-relative path to a repository.")


class AskAIRequest(BaseModel):
    question: str
    context: Optional[dict[str, Any]] = None


class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 5