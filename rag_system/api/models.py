from pydantic import BaseModel
from typing import List, Optional


class QueryRequest(BaseModel):
    """Request model for RAG query endpoint."""
    question: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for RAG query endpoint."""
    answer: str
    texts: List[str]
    highlights: List[str] = []
