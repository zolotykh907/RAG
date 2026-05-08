import logging
import os
from typing import Any, Dict, List, Optional, Union

import faiss
import numpy as np
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag_system.indexing.data_processing import normalize_text
from rag_system.indexing.indexing import Indexing
from rag_system.query.llm import LLMResponder
from rag_system.query.pipeline import RAGPipeline
from rag_system.query.query import Query
from rag_system.query.redis_client import RedisDB
from rag_system.shared.data_loader import DataLoader

logger = logging.getLogger(__name__)


class CombinedQueryService:
    """Combined query service that searches both permanent and temporary indexes."""

    def __init__(
        self,
        permanent_query: Optional[Query],
        temp_index: Any,
        temp_chunks: List[Any],
        emb_model: Any,
        k: int = 5,
        reranker: Optional[Any] = None,
        rerank_enabled: bool = False,
        rerank_candidate_k: int = 20,
    ) -> None:
        self.permanent_query = permanent_query
        self.temp_index = temp_index
        self.temp_chunks = temp_chunks
        self.emb_model = emb_model
        self.k = k
        self.reranker = reranker
        self.rerank_enabled = rerank_enabled and reranker is not None
        self.rerank_candidate_k = rerank_candidate_k

    def query(self, question: str) -> List[str]:
        """Search in both permanent and temporary indexes.

        Args:
            question: The query question.

        Returns:
            list: Combined search results from both indexes.
        """
        results: List[str] = []
        skip_rerank = self.rerank_enabled

        if self.permanent_query is not None:
            try:
                permanent_results = self.permanent_query.query(question, skip_rerank=skip_rerank)
                results.extend(permanent_results)
            except Exception as e:
                logger.warning(f"Failed to search in permanent index: {e}")

        temp_search_k = self.rerank_candidate_k if self.rerank_enabled else self.k
        try:
            query_embedding = self.emb_model.encode([question])
            query_embedding = np.array(query_embedding, dtype=np.float32)
            faiss.normalize_L2(query_embedding)
            _, indices = self.temp_index.search(
                query_embedding,
                k=min(temp_search_k, len(self.temp_chunks))
            )

            temp_results: List[str] = []
            for i in indices[0]:
                if i < len(self.temp_chunks):
                    chunk = self.temp_chunks[i]
                    if isinstance(chunk, dict):
                        temp_results.append(chunk.get('text', chunk))
                    else:
                        temp_results.append(chunk)
                else:
                    logger.warning(f"Temporary index returned invalid index {i} (max: {len(self.temp_chunks)-1})")

            results.extend(temp_results)
        except Exception as e:
            logger.warning(f"Failed to search in temporary index: {e}")

        unique_results: List[str] = list(dict.fromkeys(results))

        if self.rerank_enabled and self.reranker is not None:
            return self.reranker.rerank(question, unique_results, self.k)

        return unique_results[:self.k * 2]


def process_file_temp(
    file_path: str,
    data_loader: DataLoader,
    indexing_service: Indexing,
) -> Dict[str, Any]:
    """Process file and create temporary index with embeddings.

    Args:
        file_path: Path to the file to process.
        data_loader: DataLoader instance for loading data.
        indexing_service: Indexing service instance for embedding.

    Returns:
        dict: Dictionary with chunks and embeddings.
    """
    try:
        df = data_loader.load_data(file_path)
        filename = os.path.basename(file_path)

        df['text'] = df['text'].apply(lambda x: normalize_text(x) if pd.notna(x) else '')

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks: List[Dict[str, str]] = []
        for text in df['text']:
            if text.strip():
                split_texts = text_splitter.split_text(text)
                for chunk_text in split_texts:
                    chunks.append({
                        'text': chunk_text,
                        'source': filename
                    })

        chunk_texts = [chunk['text'] for chunk in chunks]
        embeddings = indexing_service.emb_model.encode(chunk_texts, show_progress_bar=True)
        embeddings = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings)

        temp_data: Dict[str, Any] = {
            'chunks': chunks,
            'embeddings': embeddings.tolist()
        }

        logger.info(f"Temporary indexing completed. Created {len(chunks)} chunks with embeddings.")
        return temp_data

    except Exception as e:
        logger.error(f"Temporary indexing failed: {str(e)}")
        raise


def create_combined_pipeline(
    query_service: Optional[Query],
    temp_data_list: Union[List[Dict[str, Any]], Dict[str, Any]],
    indexing_service: Indexing,
    query_config: Any,
    responder: LLMResponder,
    redis_client: Optional[RedisDB] = None,
) -> RAGPipeline:
    """Create a combined pipeline for temporary and permanent data.

    Args:
        query_service: Permanent query service instance.
        temp_data_list: List of temporary data dictionaries, each with chunks and embeddings.
        indexing_service: Indexing service instance for embedding.
        query_config: Query configuration.
        responder: LLM responder instance.
        redis_client: Redis client instance (optional).

    Returns:
        RAGPipeline: Combined RAG pipeline instance.
    """
    if isinstance(temp_data_list, dict):
        temp_data_list = [temp_data_list]

    all_chunks: List[Any] = []
    all_embeddings: List[Any] = []

    for temp_data in temp_data_list:
        if 'chunks' in temp_data and 'embeddings' in temp_data:
            all_chunks.extend(temp_data['chunks'])
            all_embeddings.extend(temp_data['embeddings'])

    if not all_embeddings:
        if query_service:
            return RAGPipeline(config=query_config, query=query_service, responder=responder, redis_client=redis_client)
        else:
            raise ValueError("No temporary or permanent data available")

    temp_embeddings = np.array(all_embeddings, dtype=np.float32)
    faiss.normalize_L2(temp_embeddings)
    temp_index = faiss.IndexFlatIP(temp_embeddings.shape[1])
    temp_index.add(temp_embeddings)

    reranker = getattr(query_service, 'reranker', None) if query_service else None
    rerank_enabled = bool(getattr(query_config, 'rerank_enabled', False))
    rerank_candidate_k = int(getattr(query_config, 'rerank_candidate_k', 20))
    k = int(getattr(query_config, 'k', 5))

    combined_query_service = CombinedQueryService(
        query_service,
        temp_index,
        all_chunks,
        indexing_service.emb_model,
        k=k,
        reranker=reranker,
        rerank_enabled=rerank_enabled,
        rerank_candidate_k=rerank_candidate_k,
    )

    combined_pipeline = RAGPipeline(
        config=query_config,
        query=combined_query_service,
        responder=responder,
        redis_client=redis_client,
    )

    return combined_pipeline
