from query import Query
from llm import LLMResponder

class RAGPipeline:
    def __init__(self, query_engine, responder):
        self.query_engine = query_engine
        self.responder = responder

    def answer(self, question: str) -> dict:
        results = self.query_engine.query(question)
        # top_contexts = [r["text"] for r in results]

        answer = self.responder.generate_answer(question, results[0])
        return {
            "answer": answer,
            "retrieved_chunks": results
        }