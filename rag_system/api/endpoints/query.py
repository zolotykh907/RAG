import logging

from fastapi import APIRouter
from fastapi import HTTPException

from rag_system.api.models import QueryRequest
from rag_system.api.models import QueryResponse
from rag_system.api.services import create_combined_pipeline
from rag_system.api.temp_storage import temp_index_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post('/query', response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Handle RAG query request.
    Args:
        request (QueryRequest): The query request containing the question and optional session ID.
    Returns:
        QueryResponse: The response containing the answer and relevant texts."""
    try:

        import rag_system.api.main as main_module

        if request.session_id and temp_index_manager.has_session(request.session_id):
            session_id = request.session_id
            temp_data = temp_index_manager.get_temp_index(session_id)

            combined_pipeline = create_combined_pipeline(
                main_module.query_service, temp_data, main_module.indexing_service,
                main_module.query_config, main_module.responder, main_module.redis_client
            )

            result = combined_pipeline.answer(request.question)

            logger.info(f"Combined query processed successfully for session {session_id}")
            return QueryResponse(answer=result['answer'], texts=result['texts'])
        else:
            if main_module.pipeline is None:
                return QueryResponse(
                    answer="Index not available. Please upload documents first.",
                    texts=[]
                )
            else:
                result = main_module.pipeline.answer(request.question)
                logger.info('Successfully processed question')
                return result

    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
