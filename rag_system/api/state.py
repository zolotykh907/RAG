import os
import threading
from typing import Any, Optional

from rag_system.indexing import Indexing
from rag_system.query.llm import LLMResponder
from rag_system.query.pipeline import RAGPipeline
from rag_system.query.query import Query
from rag_system.query.redis_client import RedisDB
from rag_system.shared.data_base import FaissDB
from rag_system.shared.data_loader import DataLoader
from rag_system.shared.logs import setup_logging
from rag_system.shared.my_config import Config as SharedConfig

_API_DIR = os.path.dirname(os.path.abspath(__file__))
_RAG_DIR = os.path.dirname(_API_DIR)

shared_config: Any = SharedConfig(os.path.join(_RAG_DIR, 'indexing', 'config.yaml'))
query_config: Any = SharedConfig(os.path.join(_RAG_DIR, 'query', 'config.yaml'))

logger = setup_logging(shared_config.logs_dir, 'rag_system')
services_lock = threading.Lock()

data_loader: Optional[DataLoader] = None
data_base: Optional[FaissDB] = None
indexing_service: Optional[Indexing] = None
query_service: Optional[Query] = None
responder: Optional[LLMResponder] = None
pipeline: Optional[RAGPipeline] = None
redis_client: Optional[RedisDB] = None


def get_indexing_service() -> Indexing:
    """Return the initialized indexing service, creating it on demand.

    Returns:
        Indexing service instance.

    Raises:
        RuntimeError: If the indexing dependencies cannot be initialized.
    """
    global data_loader, data_base, indexing_service

    with services_lock:
        if indexing_service is not None:
            return indexing_service

        try:
            logger.info("Indexing service is not initialized; retrying lazy initialization.")
            loader = data_loader or DataLoader(shared_config)
            database = data_base or FaissDB(shared_config)
            service = Indexing(shared_config, loader, database)
        except Exception as e:
            logger.error(f"Failed to lazily initialize indexing service: {str(e)}")
            raise RuntimeError(f"Indexing service failed to initialize: {str(e)}") from e

        data_loader = loader
        data_base = database
        indexing_service = service
        return service


def initialize_services() -> None:
    """Initialize monolith API services with degraded startup handling."""
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
