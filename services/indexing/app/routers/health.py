"""Health check endpoints."""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/health')
async def health_check():
    """Health check endpoint for monitoring."""
    from ..main import indexing_service, data_base

    status = {
        "service": "indexing",
        "status": "healthy",
        "indexing_service": indexing_service is not None,
        "database": data_base is not None,
    }

    logger.debug("Health check performed")
    return status


@router.get('/ready')
async def readiness_check():
    """Readiness check for Kubernetes/orchestration."""
    from ..main import indexing_service, data_base

    if indexing_service is None or data_base is None:
        return {"status": "not_ready"}, 503

    return {"status": "ready"}
