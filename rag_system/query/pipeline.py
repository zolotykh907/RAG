import hashlib
import os
from typing import Any, Dict, List, Optional

from rag_system.shared.index_snapshot import IndexSnapshotStore
from rag_system.shared.logs import setup_logging
from rag_system.query.highlight import find_highlights


def _path_signature(path: Any) -> str:
    if not path:
        return "none"

    path_str = os.path.abspath(str(path))
    try:
        stat = os.stat(path_str)
    except OSError:
        return f"{path_str}:missing"
    return f"{path_str}:{stat.st_mtime_ns}:{stat.st_size}"


def build_cache_namespace(
    config: Any,
    prefix: str = "permanent",
    extra: Optional[List[str]] = None,
) -> str:
    """Build a cache namespace from the corpus and generation settings."""
    prompt_template = str(getattr(config, "prompt_template", ""))
    prompt_hash = hashlib.sha256(prompt_template.encode("utf-8")).hexdigest()
    index_path: Any
    processed_data_path: Any
    snapshot_id: str
    try:
        artifacts = IndexSnapshotStore.from_config(config).current_artifacts()
        index_path = artifacts.index_path
        processed_data_path = artifacts.processed_data_path
        snapshot_id = artifacts.snapshot_id or "legacy"
    except Exception:
        index_path = getattr(config, 'index_path', None)
        processed_data_path = getattr(config, 'processed_data_path', None)
        snapshot_id = "unknown"

    parts = [
        prefix,
        f"snapshot={snapshot_id}",
        f"index={_path_signature(index_path)}",
        f"data={_path_signature(processed_data_path)}",
        f"llm={getattr(config, 'llm', '')}",
        f"emb={getattr(config, 'emb_model_name', '')}",
        f"prompt={prompt_hash}",
    ]
    if extra:
        parts.extend(extra)
    return "|".join(parts)


def build_chat_cache_namespace(config: Any, session_id: str) -> str:
    """Build a cache namespace isolated to a browser chat session."""
    return build_cache_namespace(
        config,
        prefix="chat",
        extra=[f"session={session_id}"],
    )


class RAGPipeline:
    """Class of pipeline for RAG."""

    def __init__(
        self,
        config: Any,
        query: Any,
        responder: Any,
        redis_client: Any,
        cache_namespace: Optional[str] = None,
    ) -> None:
        """Initialize RAG pipeline.

        Args:
            config: configuration object with parameters.
            query: component responsible for retrieving relevant texts.
            responder: component responsible for generating answers using LLM.
            redis_client: Redis cache client.
            cache_namespace: cache scope for the current corpus and generation settings.
        """
        self.query = query
        self.responder = responder
        self.logger = setup_logging(config.logs_dir, 'RAGPipeline')
        self.redis_client = redis_client
        self.cache_namespace = cache_namespace or build_cache_namespace(config)

    def answer(self, question: str) -> Dict[str, Any]:
        """Generate answer using RAG.

        Args:
            question: input question to answer.

        Returns:
            dict: generated answer, list of relevant texts, and highlight offsets.
        """
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string")

        try:
            # Try cache first, but don't fail if Redis is down
            cached_answer: Optional[Dict[str, Any]] = None
            try:
                self.logger.info("Checking Redis cache...")
                cached_answer = self.redis_client.get_from_cache(
                    question,
                    namespace=self.cache_namespace,
                )
            except Exception as e:
                self.logger.warning(f"Redis cache unavailable, skipping: {e}")

            if cached_answer:
                self.logger.info("Returning cached answer.")
                return {
                    "answer": cached_answer['answer'],
                    "texts": cached_answer['texts'],
                    "highlights": cached_answer.get('highlights', [])
                }

            self.logger.info("Searching for relevant texts for question")
            results: List[str] = self.query.query(question)

            answer: str = self.responder.generate_answer(question, results)

            highlights = find_highlights(answer, results)

            # Try to save to cache, but don't fail if Redis is down
            try:
                self.redis_client.save_to_cache(
                    question,
                    {"answer": answer, "texts": results, "highlights": highlights},
                    namespace=self.cache_namespace,
                )
            except Exception as e:
                self.logger.warning(f"Failed to save to Redis cache: {e}")

            return {
                "answer": answer,
                "texts": results,
                "highlights": highlights
            }
        except Exception as e:
            self.logger.error(f'Failed to generate answer: {str(e)}')
            raise
