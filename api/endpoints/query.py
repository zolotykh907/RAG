from fastapi import APIRouter, HTTPException
import logging

from ..models import QueryRequest, QueryResponse
from ..services import create_combined_pipeline
from ..temp_storage import temp_index_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post('/query', response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Handle RAG query request."""
    try:
        logger.info(f"Processing question: {request.question[:25]}...")
        
        # Импортируем глобальные переменные из main
        from ..main import query_service, pipeline, indexing_service, query_config, responder
        
        # Если передан session_id, используем объединенные данные
        if request.session_id and temp_index_manager.has_session(request.session_id):
            session_id = request.session_id
            temp_data = temp_index_manager.get_temp_index(session_id)
            
            # Создаем объединенный pipeline
            combined_pipeline = create_combined_pipeline(
                query_service, temp_data, indexing_service, query_config, responder
            )
            
            # Используем объединенный pipeline
            result = combined_pipeline.answer(request.question)
            
            logger.info(f"Combined query processed successfully for session {session_id}")
            return QueryResponse(answer=result['answer'], texts=result['texts'])
        else:
            # Проверяем, доступен ли обычный pipeline
            if pipeline is None:
                # Возвращаем сообщение о том, что индекс не загружен
                return QueryResponse(
                    answer="Индекс не загружен или не существует. Пожалуйста, загрузите и проиндексируйте файлы через вкладку 'Upload', или прикрепите временный файл через кнопку скрепки в чате.",
                    texts=[]
                )
            else:
                # Используем обычный pipeline
                result = pipeline.answer(request.question)
                logger.info(f'Successfully processed question')
                return result
         
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 