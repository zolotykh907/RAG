"""Health check endpoints."""

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from rag_system.services.indexing.app import state

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/health')
async def health_check():
    """Return liveness and initialization status for indexing service.

    Returns:
        Health status payload.
    """
    ready = state.indexing_service is not None and state.data_base is not None
    status = {
        "service": "indexing",
        "status": "healthy",
        "ready": ready,
        "initialization_status": state.initialization_status,
        "initialization_error": state.initialization_error,
        "indexing_service": state.indexing_service is not None,
        "database": state.data_base is not None,
    }

    logger.debug("Health check performed")
    return status


@router.get('/ready')
async def readiness_check():
    """Return readiness status for indexing traffic.

    Returns:
        Ready payload when dependencies are initialized, otherwise a 503 JSON response.
    """
    ready = state.indexing_service is not None and state.data_base is not None
    if not ready:
        return JSONResponse(
            content={
                "status": "not_ready",
                "initialization_status": state.initialization_status,
                "message": state.service_unavailable_detail(),
            },
            status_code=503,
        )

    return {
        "status": "ready",
        "initialization_status": state.initialization_status,
    }
