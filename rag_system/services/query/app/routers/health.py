"""Health check endpoints."""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/health')
async def health_check():
    """Health check endpoint for monitoring."""
    from ..main import pipeline, responder, redis_client

    status = {
        "service": "query",
        "status": "healthy",
        "pipeline_ready": pipeline is not None,
        "llm_responder": responder is not None,
        "redis_connected": redis_client is not None,
    }

    logger.debug("Health check performed")
    return status


@router.get('/ready')
async def readiness_check():
    """Readiness check for Kubernetes/orchestration."""
    from ..main import responder, redis_client

    # Query service can be ready even without pipeline (it will be initialized after first upload)
    if responder is None or redis_client is None:
        return {"status": "not_ready"}, 503

    return {"status": "ready"}
