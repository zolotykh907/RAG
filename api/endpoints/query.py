import json
import logging
from fastapi import APIRouter, HTTPException
import redis

from ..models import QueryRequest, QueryResponse
from ..services import create_combined_pipeline
from ..temp_storage import temp_index_manager

logger = logging.getLogger(__name__)
router = APIRouter()

import hashlib
def make_cache_key(query: str) -> str:
    return f"rag:{hashlib.md5(query.encode()).hexdigest()}"

redis_client = redis.Redis(host="localhost", port=6379, db=0)

def get_from_cache(query: str):
    key = make_cache_key(query)
    value = redis_client.get(key)
    if value:
        return json.loads(value)
    return None

def save_to_cache(query: str, answer: str):
    key = make_cache_key(query)
    redis_client.setex(key, 60 * 60 * 24, json.dumps(answer))  # TTL: 24 часа
    logger.info(f"Saved to cache: {query[:25]}...")


@router.post('/query', response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Handle RAG query request.
    Args:
        request (QueryRequest): The query request containing the question and optional session ID.
    Returns:
        QueryResponse: The response containing the answer and relevant texts."""
    try:
        logger.info(f"Processing question: {request.question[:25]}...")
        cached_answer = get_from_cache(request.question)
        if cached_answer:
            logger.info(f"Returning cached answer for question: {request.question[:25]}...")
            return QueryResponse(answer=cached_answer['answer'], texts=cached_answer['texts'])
        
        from ..main import query_service, pipeline, indexing_service, query_config, responder
        
        if request.session_id and temp_index_manager.has_session(request.session_id):
            session_id = request.session_id
            temp_data = temp_index_manager.get_temp_index(session_id)
            
            combined_pipeline = create_combined_pipeline(
                query_service, temp_data, indexing_service, query_config, responder
            )
            
            result = combined_pipeline.answer(request.question)
            
            logger.info(f"Combined query processed successfully for session {session_id}")
            save_to_cache(request.question, result)
            return QueryResponse(answer=result['answer'], texts=result['texts'])
        else:
            if pipeline is None:
                return QueryResponse(
                    answer="Index not available. Please upload documents first.",
                    texts=[]
                )
            else:
                result = pipeline.answer(request.question)
                logger.info(f'Successfully processed question')
                save_to_cache(request.question, result)
                return result
         
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 