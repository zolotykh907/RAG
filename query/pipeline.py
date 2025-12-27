import logging

import sys
import os
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'shared'))
from logs import setup_logging

class RAGPipeline:
    """Class of pipeline for RAG"""
    def __init__(self, config, query, responder, redis_client):
        """Initialize RAG pipeline.

        args:
            query: component responsible for retrieving relevant texts.
            responder: component responsible for generating answers using LLM.
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
            Dict[str]: generated answer and list of relevant texts.
        """
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string")
        
        try:
            self.logger.info(f"Searching for relevant texts for question in Redis cache...")
            cached_answer = self.redis_client.get_from_cache(question)
            if cached_answer:
                self.logger.info(f"Returning cached answer for question.")
                return {
                    "answer": cached_answer['answer'], 
                    "texts": cached_answer['texts']
                }
            
            self.logger.info(f"Searching for relevant texts for question")
            results = self.query.query(question)

            answer = self.responder.generate_answer(question, results)

            self.redis_client.save_to_cache(question, {"answer": answer, "texts": results})
            return {
                "answer": answer,
                "texts": results
            }
        except Exception as e:
            self.logger.error(f'Failed to generate answer: {str(e)}')
            raise
