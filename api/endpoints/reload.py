from fastapi import APIRouter, HTTPException
import logging

from query.query import Query
from query.pipeline import RAGPipeline
from shared.data_base import FaissDB
from indexing import Indexing
from shared.data_loader import DataLoader

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/reload")
async def reload_pipeline(service: str):
    """Reload pipeline configuration."""
    try:
        from ..main import (
            query_config, shared_config, responder,
            data_loader, data_base, indexing_service, query_service, pipeline
        )
        
        query_config.reload()
        shared_config.reload()
        
        if service == "query":
            new_data_base = FaissDB(shared_config)
           
            try:
                new_query_service = Query(query_config, new_data_base)
                from ..main import redis_client
                new_pipeline = RAGPipeline(config=query_config, query=new_query_service, responder=responder, redis_client=redis_client)
                
                import sys
                main_module = sys.modules['api.main']
                main_module.data_base = new_data_base
                main_module.query_service = new_query_service
                main_module.pipeline = new_pipeline
                
                logger.info('Query service and pipeline reinitialized successfully.')
                return {"message": f"{service} конфигурация перезагружена успешно", "query_service_restarted": True}
            except Exception as e:
                logger.warning(f'Failed to reinitialize Query service: {str(e)}')
                return {"message": f"{service} конфигурация перезагружена успешно", "query_service_restarted": False}
                
        elif service == "indexing":
            new_data_loader = DataLoader(shared_config)
            new_data_base = FaissDB(shared_config)
            new_indexing_service = Indexing(shared_config, new_data_loader, new_data_base)
            
            import sys
            main_module = sys.modules['api.main']
            main_module.data_loader = new_data_loader
            main_module.data_base = new_data_base
            main_module.indexing_service = new_indexing_service
            
            logger.info(f"{service} service reinitialized successfully.")
            return {"message": f"{service} configuration reloaded successfully"}
        else:
            raise ValueError("Invalid service name. Use 'query' or 'indexing'.")

    except Exception as e:
        logger.error(f"Error reload: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
