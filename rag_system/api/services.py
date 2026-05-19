import logging
import os
import hashlib
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag_system.indexing.data_processing import normalize_text
from rag_system.indexing.indexing import Indexing
from rag_system.query.llm import LLMResponder
from rag_system.query.pipeline import RAGPipeline, build_cache_namespace
from rag_system.query.query import Query
from rag_system.query.redis_client import RedisDB
from rag_system.shared.data_loader import DataLoader
from rag_system.shared.embedding_prefix import prepare_embedding_texts

logger = logging.getLogger(__name__)


def _temp_data_signature(temp_data_list: Union[List[Dict[str, Any]], Dict[str, Any]]) -> str:
    if isinstance(temp_data_list, dict):
        temp_items = [temp_data_list]
    else:
        temp_items = temp_data_list

    digest = hashlib.sha256()
    for temp_data in temp_items:
        chunks = temp_data.get('chunks', [])
        digest.update(str(len(chunks)).encode('utf-8'))
        for chunk in chunks:
            if isinstance(chunk, dict):
                source = str(chunk.get('source', ''))
                text = str(chunk.get('text', ''))
            else:
                source = ''
                text = str(chunk)
            digest.update(source.encode('utf-8'))
            digest.update(b'\0')
            digest.update(text.encode('utf-8'))
            digest.update(b'\0')
    return digest.hexdigest()


def _embedding_matrix(embeddings: Any, expected_count: int, label: str) -> np.ndarray:
    """Convert model output to a validated 2D float32 embedding matrix."""
    if expected_count <= 0:
        raise ValueError("Не удалось извлечь текст из файла. Проверьте, что документ содержит читаемый текст.")

    matrix = np.asarray(embeddings, dtype=np.float32)
    if matrix.ndim == 1:
        if expected_count != 1:
            raise ValueError(f"{label}: expected {expected_count} embeddings, got a single vector")
        matrix = matrix.reshape(1, -1)

    if matrix.ndim != 2:
        raise ValueError(f"{label}: expected a 2D embedding matrix, got shape {matrix.shape}")
    if matrix.shape[0] != expected_count:
        raise ValueError(f"{label}: expected {expected_count} embeddings, got {matrix.shape[0]}")
    if matrix.shape[1] == 0:
        raise ValueError(f"{label}: embedding dimension is empty")

    return matrix


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
        emb_model_name: Optional[str] = None,
    ) -> None:
        self.permanent_query = permanent_query
        self.temp_index = temp_index
        self.temp_chunks = temp_chunks
        self.emb_model = emb_model
        self.emb_model_name = emb_model_name
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
            prepared_question = prepare_embedding_texts(
                self.emb_model_name,
                [question],
                is_query=True,
            )
            query_embedding = self.emb_model.encode(prepared_question, convert_to_numpy=True)
            query_embedding = _embedding_matrix(query_embedding, expected_count=1, label="Query embedding")
            import faiss

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

        if not chunks:
            raise ValueError("Не удалось извлечь текст из файла. Проверьте, что документ содержит читаемый текст.")

        chunk_texts = [chunk['text'] for chunk in chunks]
        prepared_chunk_texts = prepare_embedding_texts(
            getattr(indexing_service, 'emb_model_name', None),
            chunk_texts,
            is_query=False,
        )
        embeddings = indexing_service.emb_model.encode(
            prepared_chunk_texts,
            batch_size=indexing_service.batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
        )
        embeddings = _embedding_matrix(
            embeddings,
            expected_count=len(chunk_texts),
            label="Temporary file embeddings",
        )
        import faiss

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
    session_id: Optional[str] = None,
) -> RAGPipeline:
    """Create a combined pipeline for temporary and permanent data.

    Args:
        query_service: Permanent query service instance.
        temp_data_list: List of temporary data dictionaries, each with chunks and embeddings.
        indexing_service: Indexing service instance for embedding.
        query_config: Query configuration.
        responder: LLM responder instance.
        redis_client: Redis client instance (optional).
        session_id: Temporary session ID for session-scoped cache isolation.

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

    if len(all_chunks) != len(all_embeddings):
        raise ValueError(
            f"Temporary chunks count ({len(all_chunks)}) does not match embeddings count ({len(all_embeddings)})"
        )

    temp_embeddings = _embedding_matrix(
        all_embeddings,
        expected_count=len(all_chunks),
        label="Temporary index embeddings",
    )
    import faiss

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
        emb_model_name=getattr(indexing_service, 'emb_model_name', None),
    )
    cache_namespace = build_cache_namespace(
        query_config,
        prefix="combined",
        extra=[
            f"session={session_id or 'none'}",
            f"temp={_temp_data_signature(temp_data_list)}",
        ],
    )

    combined_pipeline = RAGPipeline(
        config=query_config,
        query=combined_query_service,
        responder=responder,
        redis_client=redis_client,
        cache_namespace=cache_namespace,
    )

    return combined_pipeline
