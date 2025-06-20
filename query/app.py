from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pipeline import RAGPipeline
from query import Query
from llm import LLMResponder
from config import Config

config = Config()

app = FastAPI(title=config.api_title)

query = Query(config)

responder = LLMResponder(config)
pipeline = RAGPipeline(query_engine=query, responder=responder)

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    retrieved_chunks: list

@app.post(config.endpoint, response_model=QueryResponse)
def query_rag(request: QueryRequest):
    try:
        result = pipeline.answer(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
