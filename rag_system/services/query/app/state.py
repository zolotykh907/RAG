import os
import threading
from typing import Any, Optional

from fastapi import HTTPException

from rag_system.indexing import Indexing
from rag_system.query.llm import LLMResponder
from rag_system.query.pipeline import RAGPipeline
from rag_system.query.query import Query
from rag_system.query.redis_client import RedisDB
from rag_system.shared.data_base import FaissDB
from rag_system.shared.data_loader import DataLoader
from rag_system.shared.index_snapshot import IndexSnapshotStore
from rag_system.shared.logs import setup_logging
from rag_system.shared.my_config import Config as SharedConfig

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_RAG_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_APP_DIR)))

query_config: Any = SharedConfig(os.path.join(_RAG_DIR, 'query', 'config.yaml'))
indexing_config: Any = SharedConfig(os.path.join(_RAG_DIR, 'indexing', 'config.yaml'))
logger = setup_logging(query_config.logs_dir, 'QUERY_SERVICE')

data_base: Optional[FaissDB] = None
query_service: Optional[Query] = None
responder: Optional[LLMResponder] = None
pipeline: Optional[RAGPipeline] = None
redis_client: Optional[RedisDB] = None
temp_indexing_service: Optional[Indexing] = None
temp_indexing_lock = threading.Lock()


def initialize_temp_indexing_service() -> Indexing:
    """Initialize temporary indexing dependencies on demand.

    Returns:
        Indexing service instance for temporary session files.

    Raises:
        Exception: If temporary indexing dependencies cannot be initialized.
    """
    global temp_indexing_service

    with temp_indexing_lock:
        if temp_indexing_service is not None:
            return temp_indexing_service

        temp_indexing_service = Indexing(
            indexing_config,
            DataLoader(indexing_config),
            FaissDB(indexing_config),
        )
        logger.info('Temp indexing service initialized for session queries.')
        return temp_indexing_service


def get_temp_indexing_service() -> Indexing:
    """Return the temporary indexing service, creating it on demand.

    Returns:
        Indexing service instance for temporary session files.

    Raises:
        HTTPException: If temporary indexing dependencies cannot be initialized.
    """
    try:
        return initialize_temp_indexing_service()
    except Exception as e:
        logger.error(f'Temp indexing service unavailable: {str(e)}')
        raise HTTPException(
            status_code=503,
            detail=f"Indexing service failed to initialize: {str(e)}",
        ) from e


def initialize_services() -> None:
    """Initialize query service dependencies.

    Raises:
        Exception: If required dependencies cannot be initialized.
    """
    global data_base, query_service, responder, pipeline, redis_client, temp_indexing_service

    try:
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_client = RedisDB(host=redis_host, port=redis_port)
        logger.info('Redis client initialized successfully.')

        responder = LLMResponder(query_config)
        logger.info('LLM responder initialized successfully.')

        try:
            data_base = FaissDB(indexing_config)

            artifacts = IndexSnapshotStore.from_config(query_config).current_artifacts()
            if os.path.exists(artifacts.index_path):
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

        try:
            temp_indexing_service = initialize_temp_indexing_service()
        except Exception as e:
            logger.warning(f'Temp indexing service init failed: {str(e)}')

        logger.info('Query Service initialized.')

    except Exception as e:
        logger.error(f'Failed to initialize Query Service: {str(e)}')
        raise


def get_pipeline() -> RAGPipeline:
    """Return the initialized RAG pipeline.

    Returns:
        RAG pipeline instance.

    Raises:
        HTTPException: If the pipeline is not ready.
    """
    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Query service not ready. Please upload documents first."
        )
    return pipeline


def get_redis_client() -> RedisDB:
    """Return the initialized Redis client.

    Returns:
        Redis client wrapper.

    Raises:
        HTTPException: If Redis is unavailable.
    """
    if redis_client is None:
        raise HTTPException(
            status_code=503,
            detail="Redis client not available"
        )
    return redis_client
