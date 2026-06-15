from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rag_system.services.indexing.app import state
from rag_system.services.indexing.app.routers import config
from rag_system.services.indexing.app.routers import documents
from rag_system.services.indexing.app.routers import health
from rag_system.services.indexing.app.routers import reload
from rag_system.services.indexing.app.routers import upload


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Run FastAPI lifespan startup for the indexing service.

    Args:
        _app: FastAPI application instance.

    Returns:
        Async iterator used by FastAPI lifespan management.
    """
    await state.start_background_initialization()
    yield


app = FastAPI(
    title="RAG Indexing Service",
    description="Microservice for document indexing and embedding generation",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api/indexing", tags=["upload"])
app.include_router(documents.router, prefix="/api/indexing", tags=["documents"])
app.include_router(config.router, prefix="/api/indexing", tags=["config"])
app.include_router(reload.router, prefix="/api/indexing", tags=["reload"])
app.include_router(health.router, tags=["health"])


def __getattr__(name: str) -> Any:
    """Proxy legacy module globals to indexing state."""
    if hasattr(state, name):
        return getattr(state, name)
    if name == "_service_unavailable_detail":
        return state.service_unavailable_detail
    raise AttributeError(name)


def get_indexing_service():
    """Return the initialized indexing service."""
    return state.get_indexing_service()


def get_data_loader():
    """Return the initialized data loader."""
    return state.get_data_loader()


def get_data_base():
    """Return the initialized FAISS database wrapper."""
    return state.get_data_base()


def initialize_services() -> None:
    """Initialize indexing service dependencies."""
    state.initialize_services()


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
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
