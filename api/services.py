import logging
import os
from typing import Any, Dict

import faiss
import numpy as np
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter

from indexing.data_processing import normalize_text
from query.pipeline import RAGPipeline

logger = logging.getLogger(__name__)


class CombinedQueryService:
    """Combined query service that searches both permanent and temporary indexes."""
    def __init__(self, permanent_query, temp_index, temp_chunks, emb_model, k=5):
        self.permanent_query = permanent_query
        self.temp_index = temp_index
        self.temp_chunks = temp_chunks
        self.emb_model = emb_model
        self.k = k

    def query(self, question):
        """Search in both permanent and temporary indexes.

        Args:
            question (str): The query question.

        Returns:
            list: Combined search results from both indexes.
        """
        results = []

        if self.permanent_query is not None:
            try:
                permanent_results = self.permanent_query.query(question)
                results.extend(permanent_results)
            except Exception as e:
                logger.warning(f"Failed to search in permanent index: {e}")

        try:
            query_embedding = self.emb_model.encode([question])
            _, indices = self.temp_index.search(
                query_embedding.astype('float32'),
                k=min(self.k, len(self.temp_chunks))
            )

            temp_results = []
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

        unique_results = list(dict.fromkeys(results))
        return unique_results[:self.k * 2]


def process_file_temp(file_path: str, data_loader, indexing_service) -> Dict[str, Any]:
    """Process file and create temporary index with embeddings.

    Args:
        file_path (str): Path to the file to process.
        data_loader: DataLoader instance for loading data.
        indexing_service: Indexing service instance for embedding.

    Returns:
        dict: Dictionary with chunks and embeddings.
    """
    try:
        df = data_loader.load_data(file_path)
        filename = os.path.basename(file_path)

        df['text'] = df['text'].apply(lambda x: normalize_text(x) if pd.notna(x) else '')

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        chunks = []
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

        temp_data = {
            'chunks': chunks,
            'embeddings': embeddings.tolist()
        }

        logger.info(f"Temporary indexing completed. Created {len(chunks)} chunks with embeddings.")
        return temp_data

    except Exception as e:
        logger.error(f"Temporary indexing failed: {str(e)}")
        raise


def create_combined_pipeline(
    query_service,
    temp_data_list,
    indexing_service,
    query_config,
    responder,
    redis_client=None,
):
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

    all_chunks = []
    all_embeddings = []

    for temp_data in temp_data_list:
        if 'chunks' in temp_data and 'embeddings' in temp_data:
            all_chunks.extend(temp_data['chunks'])
            all_embeddings.extend(temp_data['embeddings'])

    if not all_embeddings:
        if query_service:
            return RAGPipeline(config=query_config, query=query_service, responder=responder, redis_client=redis_client)
        else:
            raise ValueError("No temporary or permanent data available")

    temp_embeddings = np.array(all_embeddings)
    # Use L2 metric to match the permanent index
    temp_index = faiss.IndexFlatL2(temp_embeddings.shape[1])
    temp_index.add(temp_embeddings.astype('float32'))

    combined_query_service = CombinedQueryService(
        query_service,
        temp_index,
        all_chunks,
        indexing_service.emb_model,
        k=5
    )

    combined_pipeline = RAGPipeline(config=query_config, query=combined_query_service, responder=responder, redis_client=redis_client)

    return combined_pipeline
