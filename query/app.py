import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from query.query import Query
from query.pipeline import RAGPipeline
from query.llm import LLMResponder
from query.config import Config
from query.logs import setup_logging

config = Config()
logger = setup_logging(config.logs_dir, 'RAG_API')

app = FastAPI(title=config.api_title,
              description="RAG API for question answering with context retrieval")

try:
    query = Query(config)
    responder = LLMResponder(config)
    pipeline = RAGPipeline(config=config, query=query, responder=responder)
    logger.info(f'RAG API initialized successfully.')
except Exception as e:
    logger.error(f'Failed to initialize RAG API: {str(e)}')
    raise

class QueryRequest(BaseModel):
    """Request model for RAG query endpoint."""
    question: str

class QueryResponse(BaseModel):
    """Response model for RAG query endpoint."""
    answer: str
    texts: list

@app.post(config.endpoint, response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Handle RAG query request.
    
    Args:
        request: QueryRequest containing the question.
        
    Returns:
        QueryResponse with answer and relevant texts.
    """
    try:
        logger.info(f"Processing question: {request.question[:25]}...")

        result = pipeline.answer(request.question)
        logger.info(f'Successfully processed question')

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
