import os
from pathlib import Path

from sentence_transformers import CrossEncoder

from rag_system.shared.logs import setup_logging


class CrossEncoderReranker:
    """Cross-encoder reranker for query/document pairs."""

    def __init__(self, config):
        self.logger = setup_logging(config.logs_dir, 'CrossEncoderReranker')
        self.model_name = getattr(config, 'reranker_model_name', None)
        self.enabled = bool(getattr(config, 'rerank_enabled', False))
        self.batch_size = int(getattr(config, 'rerank_batch_size', 16))
        self.max_chars = int(getattr(config, 'rerank_max_chars', 1000))
        self.device = 'cpu'
        self.model = None

        if not self.enabled:
            return

        if not self.model_name:
            self.logger.warning("Rerank is enabled, but reranker_model_name is not set. Disabling rerank.")
            self.enabled = False
            return

        try:
            self.model = self._load_local_model(self.model_name)
            self.logger.info(f"Loaded reranker model from cache: {self.model_name}")
        except Exception as e:
            self.logger.warning(f"Failed to load reranker model from cache: {e}")
            try:
                self.model = CrossEncoder(self.model_name, device=self.device)
                self.logger.info(f"Downloaded reranker model: {self.model_name}")
            except Exception as e2:
                self.logger.error(f"Failed to initialize reranker model: {e2}. Disabling rerank.")
                self.enabled = False
                self.model = None

    def _load_local_model(self, model_name):
        model_cache_name = model_name.replace('/', '--')
        cache_dir = os.path.join(
            Path.home(),
            ".cache",
            "huggingface",
            "hub",
            f"models--{model_cache_name}",
            "snapshots"
        )

        snapshots = [d for d in os.listdir(cache_dir) if os.path.isdir(os.path.join(cache_dir, d))]
        if not snapshots:
            raise FileNotFoundError(f"Model {model_name} not found in local cache {cache_dir}.")

        latest_snapshot = sorted(snapshots)[-1]
        model_path = os.path.join(cache_dir, latest_snapshot)
        return CrossEncoder(model_path, device=self.device)

    def _truncate(self, text):
        if not isinstance(text, str):
            return ""
        if self.max_chars <= 0:
            return text
        return text[: self.max_chars]

    def rerank(self, query, texts, top_k):
        if not self.enabled or self.model is None:
            return texts

        if not texts:
            return texts

        if not isinstance(query, str) or not query.strip():
            return texts

        pairs = [(query, self._truncate(t)) for t in texts]
        scores = self.model.predict(pairs, batch_size=self.batch_size, show_progress_bar=False)

        ranked = sorted(zip(texts, scores, strict=False), key=lambda x: x[1], reverse=True)
        reranked_texts = [t for t, _s in ranked]
        if top_k is None:
            return reranked_texts
        return reranked_texts[:top_k]
