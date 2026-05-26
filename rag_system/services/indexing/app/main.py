"""
Indexing Service - Handles document upload, processing, and indexing.

Responsibilities:
- Document upload and validation
- Text extraction and chunking
- Embedding generation
- Index creation and updates
- Document management (CRUD)
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from typing import Optional

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from rag_system.shared.logs import setup_logging
from rag_system.shared.my_config import Config as SharedConfig
from rag_system.shared.data_loader import DataLoader
from rag_system.shared.data_base import FaissDB
from rag_system.indexing import Indexing
import os as _os

# Configuration — resolve relative to this file so CWD doesn't matter
_APP_DIR = _os.path.dirname(_os.path.abspath(__file__))
_RAG_DIR = _os.path.dirname(_os.path.dirname(_os.path.dirname(_APP_DIR)))  # .../rag_system/
shared_config: Any = SharedConfig(_os.path.join(_RAG_DIR, 'indexing', 'config.yaml'))
logger = setup_logging(shared_config.logs_dir, 'INDEXING_SERVICE')

# Global services
data_loader: Optional[DataLoader] = None
data_base: Optional[FaissDB] = None
indexing_service: Optional[Indexing] = None
initialization_status: str = "not_started"
initialization_error: Optional[str] = None
initialization_task: Optional[asyncio.Task[None]] = None


def initialize_services() -> None:
    """Initialize indexing service dependencies.

    Raises:
        Exception: If any dependency cannot be initialized.
    """
    global data_loader, data_base, indexing_service, initialization_status, initialization_error

    initialization_status = "loading"
    initialization_error = None
    try:
        data_loader = DataLoader(shared_config)
        data_base = FaissDB(shared_config)
        indexing_service = Indexing(shared_config, data_loader, data_base)

        initialization_status = "ready"
        logger.info('Indexing service initialized successfully.')
    except Exception as e:
        data_loader = None
        data_base = None
        indexing_service = None
        initialization_status = "error"
        initialization_error = str(e)
        logger.error(f'Failed to initialize Indexing service: {str(e)}')
        raise


async def _initialize_services_on_startup() -> None:
    """Initialize services from the startup background task."""
    try:
        await asyncio.to_thread(initialize_services)
    except Exception:
        logger.exception("Background initialization failed")


async def start_background_initialization() -> None:
    """Start background initialization for heavyweight indexing dependencies."""
    global initialization_task, initialization_status

    if initialization_task is None or initialization_task.done():
        initialization_status = "starting"
        initialization_task = asyncio.create_task(_initialize_services_on_startup())


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Run FastAPI lifespan startup for the indexing service.

    Args:
        _app: FastAPI application instance.

    Returns:
        Async iterator used by FastAPI lifespan management.
    """
    await start_background_initialization()
    yield


# FastAPI rag-app
app = FastAPI(
    title="RAG Indexing Service",
    description="Microservice for document indexing and embedding generation",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Gateway will handle CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection
def get_indexing_service() -> Indexing:
    """Return the initialized indexing service.

    Returns:
        Indexing service instance.

    Raises:
        HTTPException: If the service is not ready.
    """
    if indexing_service is None:
        raise HTTPException(
            status_code=503,
            detail=_service_unavailable_detail()
        )
    return indexing_service


def get_data_loader() -> DataLoader:
    """Return the initialized data loader.

    Returns:
        DataLoader instance.

    Raises:
        HTTPException: If the service is not ready.
    """
    if data_loader is None:
        raise HTTPException(
            status_code=503,
            detail=_service_unavailable_detail()
        )
    return data_loader


def get_data_base() -> FaissDB:
    """Return the initialized FAISS database wrapper.

    Returns:
        FaissDB instance.

    Raises:
        HTTPException: If the service is not ready.
    """
    if data_base is None:
        raise HTTPException(
            status_code=503,
            detail=_service_unavailable_detail()
        )
    return data_base


def _service_unavailable_detail() -> str:
    """Return a user-facing reason for indexing service unavailability."""
    if initialization_status in {"not_started", "starting", "loading"}:
        return "Indexing service is starting. The embedding model is still loading."
    if initialization_status == "error":
        return f"Indexing service failed to initialize: {initialization_error or 'unknown error'}"
    return "Indexing service not available"


# Import routers after app initialization to avoid circular imports
from rag_system.services.indexing.app.routers import config
from rag_system.services.indexing.app.routers import documents
from rag_system.services.indexing.app.routers import health
from rag_system.services.indexing.app.routers import reload
from rag_system.services.indexing.app.routers import upload

app.include_router(upload.router, prefix="/api/indexing", tags=["upload"])
app.include_router(documents.router, prefix="/api/indexing", tags=["documents"])
app.include_router(config.router, prefix="/api/indexing", tags=["config"])
app.include_router(reload.router, prefix="/api/indexing", tags=["reload"])
app.include_router(health.router, tags=["health"])


@app.get("/")
async def root():
    """Return indexing service metadata.

    Returns:
        Service metadata payload.
    """
    return {
        "service": "RAG Indexing Service",
        "version": "2.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
