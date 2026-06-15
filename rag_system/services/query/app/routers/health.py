"""Health check endpoints."""

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from rag_system.services.query.app import state

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/health')
async def health_check():
    """Return liveness status for query service.

    Returns:
        Health status payload.
    """
    status = {
        "service": "query",
        "status": "healthy",
        "pipeline_ready": state.pipeline is not None,
        "llm_responder": state.responder is not None,
        "redis_connected": state.redis_client is not None,
    }

    logger.debug("Health check performed")
    return status


@router.get('/ready')
async def readiness_check():
    """Return readiness status for query traffic.

    Returns:
        Ready payload when dependencies are initialized, otherwise a 503 JSON response.
    """
    # Query service can be ready even without pipeline (it will be initialized after first upload)
    if state.responder is None or state.redis_client is None:
        return JSONResponse(content={"status": "not_ready"}, status_code=503)

    return {"status": "ready"}
