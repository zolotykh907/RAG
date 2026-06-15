import asyncio
import os
from typing import Any, Optional

from fastapi import HTTPException

from rag_system.indexing import Indexing
from rag_system.shared.data_base import FaissDB
from rag_system.shared.data_loader import DataLoader
from rag_system.shared.logs import setup_logging
from rag_system.shared.my_config import Config as SharedConfig

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_RAG_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_APP_DIR)))

shared_config: Any = SharedConfig(os.path.join(_RAG_DIR, 'indexing', 'config.yaml'))
logger = setup_logging(shared_config.logs_dir, 'INDEXING_SERVICE')

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
            detail=service_unavailable_detail()
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
            detail=service_unavailable_detail()
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
            detail=service_unavailable_detail()
        )
    return data_base


def service_unavailable_detail() -> str:
    """Return a user-facing reason for indexing service unavailability."""
    if initialization_status in {"not_started", "starting", "loading"}:
        return "Indexing service is starting. The embedding model is still loading."
    if initialization_status == "error":
        return f"Indexing service failed to initialize: {initialization_error or 'unknown error'}"
    return "Indexing service not available"
