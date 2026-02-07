from fastapi import APIRouter, HTTPException
import logging

from app.query.query import Query
from app.query.pipeline import RAGPipeline
from app.shared.data_base import FaissDB
from app.indexing import Indexing
from app.shared.data_loader import DataLoader

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/reload")
async def reload_pipeline(service: str):
    """Reload pipeline configuration."""
    try:
        import app.api.main as main_module
        from ..main import query_config, shared_config, responder

        query_config.reload()
        shared_config.reload()

        if service == "query":
            new_data_base = FaissDB(shared_config)

            try:
                new_query_service = Query(query_config, new_data_base)
                from ..main import redis_client
                new_pipeline = RAGPipeline(config=query_config, query=new_query_service, responder=responder, redis_client=redis_client)

                with main_module.services_lock:
                    main_module.data_base = new_data_base
                    main_module.query_service = new_query_service
                    main_module.pipeline = new_pipeline

                logger.info('Query service and pipeline reinitialized successfully.')
                return {"message": f"{service} configuration reloaded successfully", "query_service_restarted": True}
            except Exception as e:
                logger.warning(f'Failed to reinitialize Query service: {str(e)}')
                return {"message": f"{service} configuration reloaded successfully", "query_service_restarted": False}

        elif service == "indexing":
            new_data_loader = DataLoader(shared_config)
            new_data_base = FaissDB(shared_config)
            new_indexing_service = Indexing(shared_config, new_data_loader, new_data_base)

            with main_module.services_lock:
                main_module.data_loader = new_data_loader
                main_module.data_base = new_data_base
                main_module.indexing_service = new_indexing_service

            logger.info(f"{service} service reinitialized successfully.")
            return {"message": f"{service} configuration reloaded successfully"}
        else:
            raise ValueError("Invalid service name. Use 'query' or 'indexing'.")

    except Exception as e:
        logger.error(f"Error reloading {service}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
