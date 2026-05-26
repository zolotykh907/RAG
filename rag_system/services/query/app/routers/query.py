"""Query endpoints for RAG search and question answering."""

import logging
from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from typing import List
from typing import Optional

from rag_system.query.pipeline import RAGPipeline
from rag_system.query.pipeline import build_chat_cache_namespace

logger = logging.getLogger(__name__)
router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for RAG query.

    Attributes:
        question: User question to answer.
        session_id: Optional temporary session identifier.
    """
    question: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for RAG query.

    Attributes:
        answer: Generated answer text.
        texts: Retrieved context chunks.
        highlights: Disabled highlight metadata.
    """
    answer: str
    texts: List[str]
    highlights: list = []


@router.post('/ask', response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Handle RAG query request.

    Args:
        request: Query request with question and optional session_id.

    Returns:
        Answer and relevant text chunks.

    Raises:
        HTTPException: If required services are unavailable or query processing fails.
    """
    import rag_system.services.query.app.main as main_module
    pipeline = main_module.pipeline
    query_config = main_module.query_config
    query_service = main_module.query_service
    responder = main_module.responder
    redis_client = main_module.redis_client
    from rag_system.shared.temp_storage import temp_index_manager
    from rag_system.query.combined import create_combined_pipeline

    try:
        # Check if session has temporary data
        if request.session_id and temp_index_manager.has_session(request.session_id):
            session_id = request.session_id
            temp_data = temp_index_manager.get_temp_index(session_id)
            if temp_data is None:
                raise HTTPException(status_code=404, detail="Temporary session not found")

            temp_indexing = main_module.temp_indexing_service
            if temp_indexing is None:
                raise HTTPException(
                    status_code=503,
                    detail="Indexing service not available for session queries"
                )
            if responder is None:
                raise HTTPException(status_code=503, detail="LLM responder not available")

            # Create combined pipeline
            combined_pipeline = create_combined_pipeline(
                query_service,
                temp_data,
                temp_indexing,
                query_config,
                responder,
                redis_client,
                session_id=session_id,
            )

            result = combined_pipeline.answer(request.question)

            logger.info(f"Combined query processed for session {session_id}")
            return QueryResponse(answer=result['answer'], texts=result['texts'], highlights=result.get('highlights', []))

        else:
            # Use standard pipeline
            if pipeline is None:
                return QueryResponse(
                    answer="Index not available. Please upload documents first.",
                    texts=[]
                )

            if request.session_id:
                if query_service is None:
                    raise HTTPException(status_code=503, detail="Query service not available")
                if responder is None:
                    raise HTTPException(status_code=503, detail="LLM responder not available")

                session_pipeline = RAGPipeline(
                    config=query_config,
                    query=query_service,
                    responder=responder,
                    redis_client=redis_client,
                    cache_namespace=build_chat_cache_namespace(query_config, request.session_id),
                )
                result = session_pipeline.answer(request.question)
            else:
                result = pipeline.answer(request.question)

            logger.info("Query processed successfully")
            return QueryResponse(answer=result['answer'], texts=result['texts'], highlights=result.get('highlights', []))

    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
