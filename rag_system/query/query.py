import json
import os
from typing import Any, List, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from rag_system.shared.data_base import FaissDB
from rag_system.shared.logs import setup_logging
from rag_system.shared.model_loader import get_hf_cache_model_path
from rag_system.query.reranker import CrossEncoderReranker


class Query:
    """A class for preprocessing the question and semantic searching."""

    def __init__(self, config: Any, data_base: FaissDB) -> None:
        """Initialize the Query service with configuration parameters.

        Args:
            config: configuration object with parameters.
            data_base: FaissDB instance for vector search.
        """
        self.data_base = data_base
        self.index_path: str = config.index_path
        self.logs_dir: str = config.logs_dir
        self.processed_data_path: str = config.processed_data_path
        self.emb_model_name: str = config.emb_model_name
        self.emb_trust_remote_code: bool = bool(getattr(config, 'emb_trust_remote_code', False))
        self.emb_device: str = str(getattr(config, 'emb_device', 'cpu'))
        self.data: Optional[List[Any]] = None
        self.texts: Optional[List[str]] = None
        self.k: int = config.k
        self.rerank_enabled: bool = bool(getattr(config, 'rerank_enabled', False))
        self.rerank_candidate_k: int = int(getattr(config, 'rerank_candidate_k', self.k))
        self.vector_candidate_k: int = int(getattr(config, 'vector_candidate_k', max(self.rerank_candidate_k, self.k * 8)))

        self.logger = setup_logging(self.logs_dir, 'QueryService')
        self.data_base.load_index(self.index_path)
        self.load_texts()
        self.embedding_model: SentenceTransformer = self.load_local_embedding_model()
        self.reranker = CrossEncoderReranker(config)
        self.rerank_enabled = self.rerank_enabled and self.reranker.enabled

    def load_local_embedding_model(self) -> SentenceTransformer:
        try:
            model_path = get_hf_cache_model_path(self.emb_model_name)
            self.logger.info(f"Loading embedding model from local cache: {model_path}")
            return SentenceTransformer(
                model_path,
                device=self.emb_device,
                trust_remote_code=self.emb_trust_remote_code,
            )
        except FileNotFoundError:
            self.logger.warning(f"Embedding model not found in cache, downloading: {self.emb_model_name}")
            return self.download_embedding_model()
        except Exception as e:
            self.logger.error(f'Error loading model from cache: {e}')
            raise

    def download_embedding_model(self) -> SentenceTransformer:
        try:
            return SentenceTransformer(
                self.emb_model_name,
                device=self.emb_device,
                trust_remote_code=self.emb_trust_remote_code,
            )
        except Exception as e:
            self.logger.error(f'Error downloading embedding model {self.emb_model_name}: {e}')
            raise

    def load_texts(self) -> None:
        """Load the processed text from file."""
        if not os.path.exists(self.processed_data_path):
            raise FileNotFoundError(f"Data file not found at {self.processed_data_path}")

        try:
            with open(self.processed_data_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
                if not isinstance(self.data, list):
                    raise ValueError("Loaded data is not a list")

                self.texts = [item['text'] for item in self.data]
                self.logger.info(f'Loaded {len(self.texts)} texts from {self.processed_data_path}')

                if self.data_base.index is not None and self.data_base.index.ntotal != len(self.texts):
                    self.logger.error(f"The number of texts ({len(self.texts)}) != the number of vectors ({self.data_base.index.ntotal})")
                    raise ValueError("The number of texts must match the number of vectors in the DB.")
        except Exception as e:
            self.logger.error(f"Failed to load data from {self.processed_data_path}: {str(e)}")
            raise

    def normalize_text(self, text: str) -> str:
        """Normalize input text for search.

        Args:
            text: input text to normalize.

        Returns:
            str: normalized text.
        """
        if not isinstance(text, str):
            raise ValueError("Input text must be a string.")

        return text.strip()

    def query(self, request: str, skip_rerank: bool = False) -> List[str]:
        """Semantic search query.

        Args:
            request: search query string.
            skip_rerank: if True, return full candidate set without reranking or truncation.

        Returns:
            list[str]: list of top-k most similar texts from the dataset.
        """
        if not isinstance(request, str):
            raise ValueError("Request must be a string.")

        try:
            res: List[str] = []

            request = self.normalize_text(request)
            try:
                request_embedding = self.embedding_model.encode(
                    [request],
                    prompt_name="query",
                    convert_to_numpy=True
                )
            except (ValueError, TypeError):
                self.logger.warning("prompt_name='query' not supported by this model, encoding without prompt")
                request_embedding = self.embedding_model.encode(
                    [request],
                    convert_to_numpy=True
                )
            request_embedding = np.array(request_embedding, dtype=np.float32)
            faiss.normalize_L2(request_embedding)

            search_k = max(self.k, self.vector_candidate_k)
            if self.rerank_enabled:
                search_k = max(search_k, self.rerank_candidate_k)
            search_k = max(search_k, 1)

            candidate_ids, vector_scores = self.data_base.search(request_embedding, search_k)

            if self.texts is None:
                raise RuntimeError("Texts are not loaded")

            if self.data_base.index is not None and self.data_base.index.ntotal != len(self.texts):
                self.logger.error(f"The number of texts ({len(self.texts)}) != the number of vectors ({self.data_base.index.ntotal})")
                raise ValueError("The number of texts must match the number of vectors in the DB.")

            for i, idx in enumerate(candidate_ids):
                if idx < len(self.texts):
                    self.logger.debug(f"Result {i}: dense_score={vector_scores[i]:.4f}, text={self.texts[idx][:80]}...")
                    res.append(self.texts[idx])
                else:
                    self.logger.warning(f"Index {idx} is out of range for texts array (length: {len(self.texts)})")

            if skip_rerank:
                return res

            if self.rerank_enabled and self.reranker.enabled:
                return self.reranker.rerank(request, res, self.k)

            return res[: self.k]
        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")
            raise
