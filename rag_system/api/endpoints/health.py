from typing import Any, Dict, Union

from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/')
async def root() -> Dict[str, Any]:
    """Return API metadata and available endpoint paths.

    Returns:
        API metadata payload.
    """
    return {
        "message": "RAG System API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload-files",
            "upload_temp": "/upload-temp",
            "query": "/query",
            "config": "/config?service={query|indexing}",
            "reload": "/reload?service={query|indexing}",
            "clear_temp": "/clear-temp/{session_id}"
        }
    }


@router.get('/health')
async def health_check() -> Dict[str, Any]:
    """Return liveness status for the monolith API.

    Returns:
        Health status payload.
    """
    return {"status": "healthy", "message": "RAG API is running"}


@router.get('/ready')
async def readiness_check() -> Union[Dict[str, Any], JSONResponse]:
    """Return readiness status for core API services.

    Returns:
        Ready payload when services are initialized, otherwise a 503 JSON response.
    """
    import rag_system.api.main as main_module

    not_ready = []
    if main_module.responder is None:
        not_ready.append("llm_responder")
    if main_module.indexing_service is None:
        not_ready.append("indexing_service")
    if main_module.redis_client is None:
        not_ready.append("redis")

    if not_ready:
        return JSONResponse(
            content={"status": "not_ready", "missing": not_ready},
            status_code=503
        )
    return {"status": "ready"}
