import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logs import setup_logging

class RAGPipeline:
    """Class of pipeline for RAG"""
    def __init__(self, config, query, responder):
        """Initialize RAG pipeline.

        args:
            query: component responsible for retrieving relevant texts.
            responder: component responsible for generating answers using LLM.
        """
        self.query = query
        self.responder = responder
        self.logger = setup_logging(config.logs_dir, 'RAGPipeline')


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
            results = self.query.query(question)

            answer = self.responder.generate_answer(question, results)
            return {
                "answer": answer,
                "texts": results
            }
        except Exception as e:
            self.logger.error(f'Failed to generate answer: {str(e)}')
            raise
