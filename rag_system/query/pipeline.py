from typing import Any, Dict, List, Optional

from rag_system.shared.logs import setup_logging
from rag_system.query.highlight import find_highlights


class RAGPipeline:
    """Class of pipeline for RAG."""

    def __init__(
        self,
        config: Any,
        query: Any,
        responder: Any,
        redis_client: Any,
    ) -> None:
        """Initialize RAG pipeline.

        Args:
            config: configuration object with parameters.
            query: component responsible for retrieving relevant texts.
            responder: component responsible for generating answers using LLM.
            redis_client: Redis cache client.
        """
        self.query = query
        self.responder = responder
        self.logger = setup_logging(config.logs_dir, 'RAGPipeline')
        self.redis_client = redis_client

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
                cached_answer = self.redis_client.get_from_cache(question)
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
                self.redis_client.save_to_cache(question, {"answer": answer, "texts": results, "highlights": highlights})
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
