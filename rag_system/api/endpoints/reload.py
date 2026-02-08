import logging

from fastapi import APIRouter
from fastapi import HTTPException

from rag_system.query.query import Query
from rag_system.query.pipeline import RAGPipeline
from rag_system.shared.data_base import FaissDB
from rag_system.indexing import Indexing
from rag_system.shared.data_loader import DataLoader

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/reload")
async def reload_pipeline(service: str):
    """Reload pipeline configuration."""
    try:
        import rag_system.api.main as main_module

        main_module.query_config.reload()
        main_module.shared_config.reload()

        if service == "query":
            new_data_base = FaissDB(main_module.shared_config)

            try:
                new_query_service = Query(main_module.query_config, new_data_base)
                new_pipeline = RAGPipeline(
                    config=main_module.query_config,
                    query=new_query_service,
                    responder=main_module.responder,
                    redis_client=main_module.redis_client,
                )

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
            new_data_loader = DataLoader(main_module.shared_config)
            new_data_base = FaissDB(main_module.shared_config)
            new_indexing_service = Indexing(main_module.shared_config, new_data_loader, new_data_base)

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
