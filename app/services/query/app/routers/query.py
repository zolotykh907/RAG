"""Query endpoints for RAG search and question answering."""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

logger = logging.getLogger(__name__)
router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for RAG query."""
    question: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for RAG query."""
    answer: str
    texts: List[str]


@router.post('/ask', response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Handle RAG query request.

    Args:
        request: Query request with question and optional session_id.

    Returns:
        QueryResponse: Answer and relevant text chunks.
    """
    from ..main import pipeline, query_config, query_service, responder, redis_client
    from app.api.temp_storage import temp_index_manager
    from app.api.services import create_combined_pipeline

    try:
        # Check if session has temporary data
        if request.session_id and temp_index_manager.has_session(request.session_id):
            session_id = request.session_id
            temp_data = temp_index_manager.get_temp_index(session_id)

            # Get indexing service embedding model (via shared import)
            from app.indexing import Indexing
            from app.shared.my_config import Config as SharedConfig
            shared_config = SharedConfig('app/indexing/config.yaml')

            # Create minimal indexing service just for embedding model
            from app.shared.data_loader import DataLoader
            from app.shared.data_base import FaissDB
            temp_indexing = Indexing(
                shared_config,
                DataLoader(shared_config),
                FaissDB(shared_config)
            )

            # Create combined pipeline
            combined_pipeline = create_combined_pipeline(
                query_service,
                temp_data,
                temp_indexing,
                query_config,
                responder,
                redis_client
            )

            result = combined_pipeline.answer(request.question)

            logger.info(f"Combined query processed for session {session_id}")
            return QueryResponse(answer=result['answer'], texts=result['texts'])

        else:
            # Use standard pipeline
            if pipeline is None:
                return QueryResponse(
                    answer="Index not available. Please upload documents first.",
                    texts=[]
                )

            result = pipeline.answer(request.question)
            logger.info("Query processed successfully")
            return QueryResponse(answer=result['answer'], texts=result['texts'])

    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
