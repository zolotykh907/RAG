from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pipeline import RAGPipeline
from query import Query
from llm import LLMResponder

app = FastAPI(title="RAG Query API")

query = Query(index_path='/Users/igorzolotyh/RAG/data/RuBQ_index.index',
          data_path='/Users/igorzolotyh/RAG/data/good_texts.json',
          emb_model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
          )

responder = LLMResponder(model_name="llama3")
pipeline = RAGPipeline(query_engine=query, responder=responder)

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    retrieved_chunks: list

@app.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest):
    try:
        result = pipeline.answer(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
