from sentence_transformers import CrossEncoder

from rag_system.shared.logs import setup_logging
from rag_system.shared.model_loader import get_hf_cache_model_path


class CrossEncoderReranker:
    """Cross-encoder reranker for query/document pairs."""

    def __init__(self, config):
        self.logger = setup_logging(config.logs_dir, 'CrossEncoderReranker')
        self.model_name = getattr(config, 'reranker_model_name', None)
        self.enabled = bool(getattr(config, 'rerank_enabled', False))
        self.batch_size = int(getattr(config, 'rerank_batch_size', 16))
        self.max_chars = int(getattr(config, 'rerank_max_chars', 1000))
        self.score_threshold = float(getattr(config, 'rerank_score_threshold', -1e9))
        self.device = getattr(config, 'reranker_device', 'cpu')
        self.model = None

        if not self.enabled:
            return

        if not self.model_name:
            self.logger.warning("Rerank is enabled, but reranker_model_name is not set. Disabling rerank.")
            self.enabled = False
            return

        try:
            model_path = get_hf_cache_model_path(self.model_name)
            self.model = CrossEncoder(model_path, device=self.device)
            self.logger.info(f"Loaded reranker model from cache: {self.model_name}")
        except FileNotFoundError:
            self.logger.warning(f"Reranker model not found in cache, downloading: {self.model_name}")
            try:
                self.model = CrossEncoder(self.model_name, device=self.device)
                self.logger.info(f"Downloaded reranker model: {self.model_name}")
            except Exception as e2:
                self.logger.error(f"Failed to initialize reranker model: {e2}. Disabling rerank.")
                self.enabled = False
                self.model = None
        except Exception as e:
            self.logger.error(f"Failed to initialize reranker model: {e}. Disabling rerank.")
            self.enabled = False
            self.model = None

    def _truncate(self, text):
        if not isinstance(text, str):
            return ""
        if self.max_chars <= 0:
            return text
        return text[: self.max_chars]

    def rerank(self, query, texts, top_k):
        """Rerank texts by relevance to query using cross-encoder.

        Args:
            query (str): The search query.
            texts (list[str]): Candidate texts to rerank.
            top_k (int | None): Maximum number of results to return.

        Returns:
            list[str]: Reranked texts (filtered by score threshold, limited by top_k).
        """
        if not self.enabled or self.model is None:
            return texts

        if not texts:
            return texts

        if not isinstance(query, str) or not query.strip():
            return texts

        pairs = [(query, self._truncate(t)) for t in texts]
        scores = self.model.predict(pairs, batch_size=self.batch_size, show_progress_bar=False)

        ranked = sorted(zip(texts, scores, strict=False), key=lambda x: x[1], reverse=True)

        for text, score in ranked[:5]:
            self.logger.debug(f"Rerank score={score:.4f}, text={text[:80]}...")

        filtered = [(t, s) for t, s in ranked if s >= self.score_threshold]

        if not filtered:
            self.logger.warning(f"All results below score threshold ({self.score_threshold}), returning top result")
            filtered = [ranked[0]]

        reranked_texts = [t for t, _s in filtered]
        if top_k is None:
            return reranked_texts
        return reranked_texts[:top_k]
