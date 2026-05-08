from typing import Any, Dict, Union

from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/')
async def root() -> Dict[str, Any]:
    """Root endpoint with API information."""
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
    """Liveness probe — process is alive."""
    return {"status": "healthy", "message": "RAG API is running"}


@router.get('/ready')
async def readiness_check() -> Union[Dict[str, Any], JSONResponse]:
    """Readiness probe — core services are initialised and can serve requests."""
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
