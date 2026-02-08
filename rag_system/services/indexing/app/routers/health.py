"""Health check endpoints."""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/health')
async def health_check():
    """Health check endpoint for monitoring."""
    import rag_system.services.indexing.app.main as main_module

    status = {
        "service": "indexing",
        "status": "healthy",
        "indexing_service": main_module.indexing_service is not None,
        "database": main_module.data_base is not None,
    }

    logger.debug("Health check performed")
    return status


@router.get('/ready')
async def readiness_check():
    """Readiness check for Kubernetes/orchestration."""
    import rag_system.services.indexing.app.main as main_module

    if main_module.indexing_service is None or main_module.data_base is None:
        return {"status": "not_ready"}, 503

    return {"status": "ready"}
