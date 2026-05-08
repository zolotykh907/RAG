"""Health check endpoints."""

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/health')
async def health_check():
    """Liveness endpoint for monitoring."""
    import rag_system.services.indexing.app.main as main_module

    ready = main_module.indexing_service is not None and main_module.data_base is not None
    status = {
        "service": "indexing",
        "status": "healthy",
        "ready": ready,
        "initialization_status": main_module.initialization_status,
        "initialization_error": main_module.initialization_error,
        "indexing_service": main_module.indexing_service is not None,
        "database": main_module.data_base is not None,
    }

    logger.debug("Health check performed")
    return status


@router.get('/ready')
async def readiness_check():
    """Readiness check for routing and user-facing upload state."""
    import rag_system.services.indexing.app.main as main_module

    ready = main_module.indexing_service is not None and main_module.data_base is not None
    if not ready:
        return JSONResponse(
            content={
                "status": "not_ready",
                "initialization_status": main_module.initialization_status,
                "message": main_module._service_unavailable_detail(),
            },
            status_code=503,
        )

    return {
        "status": "ready",
        "initialization_status": main_module.initialization_status,
    }
