from pydantic import BaseModel
from typing import List, Optional


class QueryRequest(BaseModel):
    """Request model for RAG query endpoint.

    Attributes:
        question: User question to answer.
        session_id: Optional temporary session identifier.
    """
    question: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for RAG query endpoint.

    Attributes:
        answer: Generated answer text.
        texts: Retrieved context chunks.
        highlights: Disabled highlight metadata.
    """
    answer: str
    texts: List[str]
    highlights: List[str] = []
