import logging

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from rag_system.api import state
from rag_system.api.models import QueryRequest
from rag_system.api.models import QueryResponse
from rag_system.query.combined import create_combined_pipeline
from rag_system.query.pipeline import RAGPipeline
from rag_system.query.pipeline import build_chat_cache_namespace
from rag_system.shared.temp_storage import temp_index_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post('/query', response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Handle a RAG query request.

    Args:
        request: Query payload with question and optional session ID.

    Returns:
        Query response payload or a JSON response when the index is unavailable.

    Raises:
        HTTPException: If required services are unavailable or query processing fails.
    """
    # Snapshot global state under lock to avoid races with concurrent uploads/reloads
    with state.services_lock:
        pipeline = state.pipeline
        query_service = state.query_service
        responder = state.responder
        indexing_service = state.indexing_service
        redis_client = state.redis_client
        query_config = state.query_config

    try:
        if request.session_id and temp_index_manager.has_session(request.session_id):
            temp_data = temp_index_manager.get_temp_index(request.session_id)
            if temp_data is None:
                raise HTTPException(status_code=404, detail="Temporary session not found")
            if indexing_service is None:
                raise HTTPException(status_code=503, detail="Indexing service not available for session queries")
            if responder is None:
                raise HTTPException(status_code=503, detail="LLM responder not available")

            combined_pipeline = create_combined_pipeline(
                query_service, temp_data, indexing_service,
                query_config, responder, redis_client,
                session_id=request.session_id,
            )
            result = combined_pipeline.answer(request.question)
            logger.info(f"Combined query processed for session {request.session_id}")
            return QueryResponse(
                answer=result['answer'],
                texts=result['texts'],
                highlights=result.get('highlights', [])
            )

        if pipeline is None:
            return JSONResponse(
                content={"answer": "Index not available. Please upload documents first.", "texts": [], "highlights": []},
                status_code=503
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
        logger.info('Successfully processed question')
        return result

    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Query processing failed")
