from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Request model for RAG query endpoint."""
    question: str
    session_id: str = None


class QueryResponse(BaseModel):
    """Response model for RAG query endpoint."""
    answer: str
    texts: list 