# import sys
# import os

# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel

# from query.query import Query
# from query.pipeline import RAGPipeline
# from query.llm import LLMResponder
# from query.config import Config

# sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'shared'))
# from logs import setup_logging
# from data_base import ChromaDB, FaissDB

# config = Config()
# logger = setup_logging(config.logs_dir, 'RAG_API')

# app = FastAPI(title=config.api_title,
#               description="RAG API for question answering with context retrieval")

# try:
#     data_base = ChromaDB(config)
#     query = Query(config, data_base)
#     responder = LLMResponder(config)
#     pipeline = RAGPipeline(config=config, query=query, responder=responder)
#     logger.info(f'RAG API initialized successfully.')
# except Exception as e:
#     logger.error(f'Failed to initialize RAG API: {str(e)}')
#     raise

# class QueryRequest(BaseModel):
#     """Request model for RAG query endpoint."""
#     question: str

# class QueryResponse(BaseModel):
#     """Response model for RAG query endpoint."""
#     answer: str
#     texts: list

# @app.post(config.endpoint, response_model=QueryResponse)
# async def query_rag(request: QueryRequest):
#     """Handle RAG query request.

#     Args:
#         request: QueryRequest containing the question.

#     Returns:
#         QueryResponse with answer and relevant texts.
#     """
#     try:
#         logger.info(f"Processing question: {request.question[:25]}...")

#         result = pipeline.answer(request.question)
#         logger.info(f'Successfully processed question')

#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from query.query import Query
from query.pipeline import RAGPipeline
from query.llm import LLMResponder
from query.config import Config
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'shared'))
from logs import setup_logging
from data_base import FaissDB

config = Config()
logger = setup_logging(config.logs_dir, 'RAG_API')

app = FastAPI(title='API',
              description="RAG API for question answering with context retrieval")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files on /static path
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

try:
    data_base = FaissDB(config)
    query = Query(config, data_base)
    responder = LLMResponder(config)
    pipeline = RAGPipeline(config=config, query=query, responder=responder)
    logger.info('RAG API initialized successfully.')
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

@app.get("/")
async def root():
    """Serve the main HTML page."""
    static_path = Path(__file__).parent.parent / "static" / "index.html"
    if static_path.exists():
        return FileResponse(static_path)
    else:
        return {"message": "RAG API is running. Static files not found."}

@app.post('/query', response_model=QueryResponse)
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
        logger.info('Successfully processed question')

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "RAG API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
