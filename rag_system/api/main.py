import os
import threading
from typing import Any
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rag_system.shared.logs import setup_logging
from rag_system.shared.my_config import Config as SharedConfig
from rag_system.shared.data_loader import DataLoader
from rag_system.shared.data_base import FaissDB
from rag_system.indexing import Indexing
from rag_system.query.query import Query
from rag_system.query.pipeline import RAGPipeline
from rag_system.query.llm import LLMResponder
from rag_system.query.redis_client import RedisDB

from rag_system.api.endpoints import config
from rag_system.api.endpoints import documents
from rag_system.api.endpoints import health
from rag_system.api.endpoints import query
from rag_system.api.endpoints import reload
from rag_system.api.endpoints import upload

shared_config: Any = SharedConfig('rag_system/indexing/config.yaml')
query_config: Any = SharedConfig('rag_system/query/config.yaml')

logger = setup_logging(shared_config.logs_dir, 'rag_system')

# Lock for thread-safe modification of global services
services_lock = threading.Lock()

data_loader: Optional[DataLoader] = None
data_base: Optional[FaissDB] = None
indexing_service: Optional[Indexing] = None
query_service: Optional[Query] = None
responder: Optional[LLMResponder] = None
pipeline: Optional[RAGPipeline] = None
redis_client: Optional[RedisDB] = None


def initialize_services():
    """Initialize all services with error handling."""
    global data_loader, data_base, indexing_service, query_service, responder, pipeline, redis_client

    try:
        data_loader = DataLoader(shared_config)
        data_base = FaissDB(shared_config)
        indexing_service = Indexing(shared_config, data_loader, data_base)

        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_client = RedisDB(host=redis_host, port=redis_port)

        try:
            query_service = Query(query_config, data_base)
            logger.info('Query service initialized successfully.')
        except Exception as e:
            logger.warning(f'Failed to initialize Query service (index may not exist): {str(e)}')
            query_service = None

        try:
            responder = LLMResponder(query_config)
            logger.info('LLM responder initialized successfully.')
        except Exception as e:
            logger.error(f'Failed to initialize LLM responder: {str(e)}')
            raise

        if query_service is not None:
            pipeline = RAGPipeline(config=query_config, query=query_service, responder=responder, redis_client=redis_client)
            logger.info('RAG pipeline initialized successfully.')
        else:
            logger.warning('RAG pipeline not initialized - no index available.')

        logger.info('RAG API initialized successfully.')
    except Exception as e:
        logger.error(f'Failed to initialize RAG API: {str(e)}')
        logger.warning('Continuing with limited functionality...')


initialize_services()

app = FastAPI(
    title="RAG System API",
    description="Unified API for document indexing and RAG querying",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router, tags=["query"])
app.include_router(upload.router, tags=["upload"])
app.include_router(config.router, tags=["config"])
app.include_router(health.router, tags=["health"])
app.include_router(reload.router, tags=["reload"])
app.include_router(documents.router, tags=["documents"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
