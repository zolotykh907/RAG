from shared.logs import setup_logging


class RAGPipeline:
    """Class of pipeline for RAG."""
    def __init__(self, config, query, responder, redis_client):
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

    def answer(self, question):
        """Generate answer using RAG.

        Args:
            question (str): input question to answer.

        Returns:
            dict: generated answer and list of relevant texts.
        """
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string")

        try:
            # Try cache first, but don't fail if Redis is down
            cached_answer = None
            try:
                self.logger.info("Checking Redis cache...")
                cached_answer = self.redis_client.get_from_cache(question)
            except Exception as e:
                self.logger.warning(f"Redis cache unavailable, skipping: {e}")

            if cached_answer:
                self.logger.info("Returning cached answer.")
                return {
                    "answer": cached_answer['answer'],
                    "texts": cached_answer['texts']
                }

            self.logger.info("Searching for relevant texts for question")
            results = self.query.query(question)

            answer = self.responder.generate_answer(question, results)

            # Try to save to cache, but don't fail if Redis is down
            try:
                self.redis_client.save_to_cache(question, {"answer": answer, "texts": results})
            except Exception as e:
                self.logger.warning(f"Failed to save to Redis cache: {e}")

            return {
                "answer": answer,
                "texts": results
            }
        except Exception as e:
            self.logger.error(f'Failed to generate answer: {str(e)}')
            raise
