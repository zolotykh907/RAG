import heapq
import json
import math
import os
import re
from collections import defaultdict

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from rag_system.shared.logs import setup_logging
from rag_system.shared.model_loader import get_hf_cache_model_path
from rag_system.query.reranker import CrossEncoderReranker


class Query:
    """A class for preprocessing the question and semantic searching."""
    def __init__(self, config, data_base):
        """Initialize the Query service with configuration parameters.

        Args:
            config: configuration object with parameters.
        """
        self.data_base = data_base
        self.index_path = config.index_path
        self.logs_dir = config.logs_dir
        self.processed_data_path = config.processed_data_path
        self.emb_model_name = config.emb_model_name
        self.data = None
        self.texts = None
        self.k = config.k
        self.rerank_enabled = bool(getattr(config, 'rerank_enabled', False))
        self.rerank_candidate_k = int(getattr(config, 'rerank_candidate_k', self.k))
        self.vector_candidate_k = int(getattr(config, 'vector_candidate_k', max(self.rerank_candidate_k, self.k * 8)))

        # Hybrid retrieval config (dense + lexical BM25 + weighted RRF fusion)
        self.hybrid_enabled = bool(getattr(config, 'hybrid_enabled', True))
        self.lexical_candidate_k = int(getattr(config, 'lexical_candidate_k', self.vector_candidate_k))
        self.hybrid_vector_weight = float(getattr(config, 'hybrid_vector_weight', 1.0))
        self.hybrid_lexical_weight = float(getattr(config, 'hybrid_lexical_weight', 0.8))
        self.hybrid_rrf_k = int(getattr(config, 'hybrid_rrf_k', 60))
        self.bm25_k1 = float(getattr(config, 'bm25_k1', 1.5))
        self.bm25_b = float(getattr(config, 'bm25_b', 0.75))
        self.token_pattern = re.compile(r"[\w\-]+", flags=re.UNICODE)
        self.postings = {}
        self.doc_len = np.array([], dtype=np.int32)
        self.avg_doc_len = 0.0
        self.num_docs = 0

        self.logger = setup_logging(self.logs_dir, 'QueryService')
        self.data_base.load_index(self.index_path)
        self.load_texts()
        self.embedding_model = self.load_local_embedding_model()
        self.reranker = CrossEncoderReranker(config)
        self.rerank_enabled = self.rerank_enabled and self.reranker.enabled

    def load_local_embedding_model(self):
        try:
            model_path = get_hf_cache_model_path(self.emb_model_name)
            self.logger.info(f"Loading embedding model from local cache: {model_path}")
            return SentenceTransformer(model_path, device='cpu')
        except Exception as e:
            self.logger.error(f'Error loading model from cache: {e}')
            raise

    def load_texts(self):
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

                if self.hybrid_enabled:
                    self._build_lexical_index()
        except Exception as e:
            self.logger.error(f"Failed to load data from {self.processed_data_path}: {str(e)}")
            raise

    def normalize_text(self, text):
        """Normalize input text for search.

        Args:
            text (str): input text to normalize.

        Returns:
            str: normalized text.
        """
        if not isinstance(text, str):
            raise ValueError("Input text must be a string.")

        return text.strip()

    def _tokenize(self, text):
        if not isinstance(text, str):
            return []
        return self.token_pattern.findall(text.lower())

    def _build_lexical_index(self):
        """Build in-memory BM25 structures for hybrid retrieval."""
        if self.texts is None:
            self.postings = {}
            self.doc_len = np.array([], dtype=np.int32)
            self.avg_doc_len = 0.0
            self.num_docs = 0
            return

        self.num_docs = len(self.texts)
        self.doc_len = np.zeros(self.num_docs, dtype=np.int32)
        raw_postings = defaultdict(dict)

        for doc_id, text in enumerate(self.texts):
            token_freq = defaultdict(int)
            for token in self._tokenize(text):
                token_freq[token] += 1

            self.doc_len[doc_id] = sum(token_freq.values())
            for token, tf in token_freq.items():
                raw_postings[token][doc_id] = tf

        self.postings = {
            token: (len(docs_map), list(docs_map.items()))
            for token, docs_map in raw_postings.items()
        }
        self.avg_doc_len = float(np.mean(self.doc_len)) if self.num_docs > 0 else 0.0
        self.logger.info(
            f"Built lexical index for hybrid retrieval: docs={self.num_docs}, vocab={len(self.postings)}"
        )

    def _lexical_search(self, request, top_k):
        """Lexical BM25 retrieval over in-memory postings."""
        if not self.hybrid_enabled or top_k <= 0 or self.num_docs == 0 or not self.postings:
            return np.array([], dtype=np.int64), np.array([], dtype=np.float32)

        tokens = self._tokenize(request)
        if not tokens:
            return np.array([], dtype=np.int64), np.array([], dtype=np.float32)

        bm25_scores = defaultdict(float)
        avg_dl = self.avg_doc_len if self.avg_doc_len > 0 else 1.0

        for token in set(tokens):
            posting = self.postings.get(token)
            if posting is None:
                continue

            df, docs = posting
            idf = math.log(1.0 + (self.num_docs - df + 0.5) / (df + 0.5))

            for doc_id, tf in docs:
                dl = max(int(self.doc_len[doc_id]), 1)
                denom = tf + self.bm25_k1 * (1.0 - self.bm25_b + self.bm25_b * (dl / avg_dl))
                bm25_scores[doc_id] += idf * ((tf * (self.bm25_k1 + 1.0)) / denom)

        if not bm25_scores:
            return np.array([], dtype=np.int64), np.array([], dtype=np.float32)

        ranked = heapq.nlargest(top_k, bm25_scores.items(), key=lambda x: x[1])
        ids = np.array([doc_id for doc_id, _score in ranked], dtype=np.int64)
        scores = np.array([score for _doc_id, score in ranked], dtype=np.float32)
        return ids, scores

    def _fuse_rankings(self, vector_ids, lexical_ids, top_k):
        """Fuse dense and lexical rankings with weighted reciprocal rank fusion."""
        if top_k <= 0:
            return np.array([], dtype=np.int64)

        fused_scores = {}

        for rank, doc_id in enumerate(vector_ids, start=1):
            doc_id = int(doc_id)
            fused_scores[doc_id] = (
                fused_scores.get(doc_id, 0.0)
                + self.hybrid_vector_weight / (self.hybrid_rrf_k + rank)
            )

        for rank, doc_id in enumerate(lexical_ids, start=1):
            doc_id = int(doc_id)
            fused_scores[doc_id] = (
                fused_scores.get(doc_id, 0.0)
                + self.hybrid_lexical_weight / (self.hybrid_rrf_k + rank)
            )

        if not fused_scores:
            return np.array([], dtype=np.int64)

        ranked = heapq.nlargest(top_k, fused_scores.items(), key=lambda x: x[1])
        return np.array([doc_id for doc_id, _score in ranked], dtype=np.int64)

    def query(self, request, skip_rerank=False):
        """Semantic search query.

        Args:
            request (str): search query string.
            skip_rerank (bool): if True, return full candidate set without reranking or truncation.

        Returns:
            list[str]: list of top-k most similar texts from the dataset
        """
        if not isinstance(request, str):
            raise ValueError("Request must be a string.")

        try:
            res = []

            request = self.normalize_text(request)
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

            vector_ids, vector_scores = self.data_base.search(request_embedding, search_k)
            candidate_ids = vector_ids
            lexical_ids = np.array([], dtype=np.int64)

            if self.hybrid_enabled:
                lexical_k = max(self.lexical_candidate_k, search_k)
                lexical_ids, _ = self._lexical_search(request, lexical_k)
                candidate_ids = self._fuse_rankings(vector_ids, lexical_ids, search_k)

                if candidate_ids.size == 0:
                    candidate_ids = vector_ids

                self.logger.debug(
                    "Hybrid retrieval: vector=%s lexical=%s fused=%s",
                    len(vector_ids),
                    len(lexical_ids),
                    len(candidate_ids),
                )

            if self.texts is None:
                raise RuntimeError("Texts are not loaded")

            if self.data_base.index is not None and self.data_base.index.ntotal != len(self.texts):
                self.logger.error(f"The number of texts ({len(self.texts)}) != the number of vectors ({self.data_base.index.ntotal})")
                raise ValueError("The number of texts must match the number of vectors in the DB.")

            vector_score_by_id = {int(doc_id): float(score) for doc_id, score in zip(vector_ids, vector_scores, strict=False)}

            for i, idx in enumerate(candidate_ids):
                if idx < len(self.texts):
                    dense_score = vector_score_by_id.get(int(idx), float('nan'))
                    self.logger.debug(f"Result {i}: dense_score={dense_score:.4f}, text={self.texts[idx][:80]}...")
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
