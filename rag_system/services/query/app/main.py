"""
Query Service - Handles RAG queries and semantic search.

Responsibilities:
- Semantic search in vector database
- RAG pipeline execution
- LLM communication
- Query caching via Redis
- Temporary session-based queries
"""

import os
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from rag_system.query.pipeline import RAGPipeline
from rag_system.query.query import Query
from rag_system.shared.data_base import FaissDB
from rag_system.shared.index_snapshot import IndexSnapshotStore
from rag_system.services.query.app import state
from rag_system.services.query.app.routers import config
from rag_system.services.query.app.routers import health
from rag_system.services.query.app.routers import query
from rag_system.services.query.app.routers import sessions

state.initialize_services()

app = FastAPI(
    title="RAG Query Service",
    description="Microservice for RAG queries and semantic search",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router, prefix="/api/query", tags=["query"])
app.include_router(sessions.router, prefix="/api/query", tags=["sessions"])
app.include_router(config.router, prefix="/api/query", tags=["config"])
app.include_router(health.router, tags=["health"])


def __getattr__(name: str) -> Any:
    """Proxy legacy module globals to query state."""
    if hasattr(state, name):
        return getattr(state, name)
    raise AttributeError(name)


def get_pipeline():
    """Return the initialized RAG pipeline."""
    return state.get_pipeline()


def get_redis_client():
    """Return the initialized Redis client."""
    return state.get_redis_client()


@app.get("/")
async def root():
    """Return query service metadata.

    Returns:
        Service metadata payload.
    """
    return {
        "service": "RAG Query Service",
        "version": "2.0.0",
        "status": "running",
        "pipeline_ready": state.pipeline is not None
    }


@app.post("/api/query/reload")
async def reload_index():
    """Reload index after indexing service updates.

    Returns:
        Reload status payload.

    Raises:
        HTTPException: If index reload fails.
    """
    try:
        state.query_config.reload()
        state.indexing_config.reload()

        artifacts = IndexSnapshotStore.from_config(state.query_config).current_artifacts()
        if not artifacts.index_path or not os.path.exists(artifacts.index_path):
            state.logger.warning("Index file not found for reload")
            return {"status": "no_index", "message": "No index file found"}

        if state.data_base is None:
            state.data_base = FaissDB(state.indexing_config)

        state.data_base.load_index(artifacts.index_path)

        state.query_service = Query(state.query_config, state.data_base)
        state.pipeline = RAGPipeline(
            config=state.query_config,
            query=state.query_service,
            responder=state.responder,
            redis_client=state.redis_client
        )

        if state.redis_client is not None:
            state.redis_client.flush_cache()

        state.logger.info("Index reloaded successfully")
        return {"status": "reloaded", "message": "Index reloaded successfully"}

    except Exception as e:
        state.logger.error(f"Failed to reload index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query/reset")
async def reset_service():
    """Reset query service when index is cleared.

    Returns:
        Reset status payload.
    """
    state.query_service = None
    state.pipeline = None

    state.logger.info("Query service reset")
    return {"status": "reset", "message": "Query service reset successfully"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
