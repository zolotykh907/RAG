import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAGPipeline")

class RAGPipeline:
    """Class of pipeline for RAG"""
    def __init__(self, query, responder):
        """Initialize RAG pipeline.

        args:
            query: component responsible for retrieving relevant texts.
            responder: component responsible for generating answers using LLM.
        """
        self.query = query
        self.responder = responder

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
            
            # top_contexts = [r["text"] for r in results]

            answer = self.responder.generate_answer(question, results[0])
            return {
                "answer": answer,
                "texts": results
            }
        except Exception as e:
            logger.error(f'Failed to generate answer: {str(e)}')
            raise
