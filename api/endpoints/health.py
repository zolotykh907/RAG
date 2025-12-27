from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/')
async def root():
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
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "RAG API is running"} 