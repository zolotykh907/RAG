"""
Query Service - Handles RAG queries and semantic search.

Responsibilities:
- Semantic search in vector database
- RAG pipeline execution
- LLM communication
- Query caching via Redis
- Temporary session-based queries
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'shared'))
sys.path.append(str(project_root / 'query'))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from logs import setup_logging
from my_config import Config as SharedConfig
from shared.data_base import FaissDB
from query.query import Query
from query.pipeline import RAGPipeline
from query.llm import LLMResponder
from query.redis_client import RedisDB

# Configuration
query_config = SharedConfig('query/config.yaml')
logger = setup_logging(query_config.logs_dir, 'QUERY_SERVICE')

# Global services
data_base: FaissDB = None
query_service: Query = None
responder: LLMResponder = None
pipeline: RAGPipeline = None
redis_client: RedisDB = None


def initialize_services():
    """Initialize query services with error handling."""
    global data_base, query_service, responder, pipeline, redis_client

    try:
        # Initialize Redis
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_client = RedisDB(host=redis_host, port=redis_port)
        logger.info('Redis client initialized successfully.')

        # Initialize LLM responder (required)
        responder = LLMResponder(query_config)
        logger.info('LLM responder initialized successfully.')

        # Initialize database and query service (may fail if no index exists yet)
        try:
            shared_config = SharedConfig('indexing/config.yaml')
            data_base = FaissDB(shared_config)

            if os.path.exists(query_config.index_path):
                query_service = Query(query_config, data_base)
                pipeline = RAGPipeline(
                    config=query_config,
                    query=query_service,
                    responder=responder,
                    redis_client=redis_client
                )
                logger.info('Query service and RAG pipeline initialized successfully.')
            else:
                logger.warning('Index not found. Query service will be initialized after first indexing.')

        except Exception as e:
            logger.warning(f'Query service initialization skipped (no index): {str(e)}')

        logger.info('Query Service initialized.')

    except Exception as e:
        logger.error(f'Failed to initialize Query Service: {str(e)}')
        raise


initialize_services()

# FastAPI app
app = FastAPI(
    title="RAG Query Service",
    description="Microservice for RAG queries and semantic search",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Gateway handles CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection
def get_pipeline() -> RAGPipeline:
    """Get RAG pipeline instance."""
    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Query service not ready. Please upload documents first."
        )
    return pipeline


def get_redis_client() -> RedisDB:
    """Get Redis client instance."""
    if redis_client is None:
        raise HTTPException(
            status_code=503,
            detail="Redis client not available"
        )
    return redis_client


# Import routers
from app.routers import query, sessions, health

app.include_router(query.router, prefix="/api/query", tags=["query"])
app.include_router(sessions.router, prefix="/api/query", tags=["sessions"])
app.include_router(health.router, tags=["health"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "RAG Query Service",
        "version": "2.0.0",
        "status": "running",
        "pipeline_ready": pipeline is not None
    }


@app.post("/api/query/reload")
async def reload_index():
    """Reload index after indexing service updates.

    Called by indexing service after new documents are indexed.
    """
    global query_service, pipeline, data_base

    try:
        if not os.path.exists(query_config.index_path):
            logger.warning("Index file not found for reload")
            return {"status": "no_index", "message": "No index file found"}

        # Reload database index
        if data_base is None:
            shared_config = SharedConfig('indexing/config.yaml')
            data_base = FaissDB(shared_config)

        data_base.load_index(query_config.index_path)

        # Reinitialize query service and pipeline
        query_service = Query(query_config, data_base)
        pipeline = RAGPipeline(
            config=query_config,
            query=query_service,
            responder=responder,
            redis_client=redis_client
        )

        logger.info("Index reloaded successfully")
        return {"status": "reloaded", "message": "Index reloaded successfully"}

    except Exception as e:
        logger.error(f"Failed to reload index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query/reset")
async def reset_service():
    """Reset query service when index is cleared.

    Called by indexing service when all documents are deleted.
    """
    global query_service, pipeline

    query_service = None
    pipeline = None

    logger.info("Query service reset")
    return {"status": "reset", "message": "Query service reset successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
