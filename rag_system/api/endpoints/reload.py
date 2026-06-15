import logging

from fastapi import APIRouter
from fastapi import HTTPException

from rag_system.api import state
from rag_system.query.query import Query
from rag_system.query.pipeline import RAGPipeline
from rag_system.shared.data_base import FaissDB
from rag_system.indexing import Indexing
from rag_system.shared.data_loader import DataLoader

logger = logging.getLogger(__name__)
router = APIRouter()

_VALID_SERVICES = {"query", "indexing"}


@router.post("/reload")
async def reload_pipeline(service: str):
    """Reload runtime services after configuration changes.

    Args:
        service: Service name to reload.

    Returns:
        Reload status payload.

    Raises:
        HTTPException: If the service name is invalid or reload fails.
    """
    if service not in _VALID_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service '{service}'. Use 'query' or 'indexing'."
        )

    try:
        state.query_config.reload()
        state.shared_config.reload()

        if service == "query":
            new_data_base = FaissDB(state.shared_config)

            try:
                new_query_service = Query(state.query_config, new_data_base)
                new_pipeline = RAGPipeline(
                    config=state.query_config,
                    query=new_query_service,
                    responder=state.responder,
                    redis_client=state.redis_client,
                )

                with state.services_lock:
                    state.data_base = new_data_base
                    state.query_service = new_query_service
                    state.pipeline = new_pipeline

                logger.info('Query service and pipeline reinitialized successfully.')
                return {"message": "query configuration reloaded successfully", "query_service_restarted": True}
            except Exception as e:
                logger.warning(f'Failed to reinitialize Query service: {str(e)}')
                return {"message": "query configuration reloaded successfully", "query_service_restarted": False}

        else:  # service == "indexing"
            new_data_loader = DataLoader(state.shared_config)
            new_data_base = FaissDB(state.shared_config)
            new_indexing_service = Indexing(state.shared_config, new_data_loader, new_data_base)

            with state.services_lock:
                state.data_loader = new_data_loader
                state.data_base = new_data_base
                state.indexing_service = new_indexing_service

            logger.info("Indexing service reinitialized successfully.")
            return {"message": "indexing configuration reloaded successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reloading {service}: {e}")
        raise HTTPException(status_code=500, detail="Reload failed")
