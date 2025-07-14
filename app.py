import sys
import os
import shutil
from tempfile import TemporaryDirectory

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shared'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'indexing'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'query'))

from logs import setup_logging
from my_config import Config as SharedConfig
from data_loader import DataLoader
from data_base import FaissDB, ChromaDB

from indexing import Indexing

from query.query import Query
from query.pipeline import RAGPipeline
from query.llm import LLMResponder
from query.config import Config as QueryConfig

import yaml
from fastapi.responses import JSONResponse
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'query', 'config.yaml')

shared_config = SharedConfig()
query_config = QueryConfig()

logger = setup_logging(shared_config.logs_dir, 'RAG_API')

try:
    data_loader = DataLoader(shared_config)
    data_base = FaissDB(shared_config)
    indexing_service = Indexing(shared_config, data_loader, data_base)
    
    query_service = Query(query_config, data_base)
    responder = LLMResponder(query_config)
    pipeline = RAGPipeline(config=query_config, query=query_service, responder=responder)
    
    logger.info('RAG API initialized successfully.')
except Exception as e:
    logger.error(f'Failed to initialize RAG API: {str(e)}')
    raise

app = FastAPI(
    title="RAG System API",
    description="Unified API for document indexing and RAG querying",
    version="1.0.0"
)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    """Request model for RAG query endpoint."""
    question: str

class QueryResponse(BaseModel):
    """Response model for RAG query endpoint."""
    answer: str
    texts: list

@app.get("/config")
async def get_config():
    """Получить текущую конфигурацию."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config_data = yaml.safe_load(f)
        return config_data
    except Exception as e:
        logger.error(f"Не удалось прочитать конфигурацию: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при чтении конфигурации")


@app.post("/config")
async def update_config(new_config: dict):
    """Обновить конфигурацию."""
    try:
        def str_presenter(dumper, data):
            """Кастомный представление строк для многострочного текста."""
            if '\n' in data:
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data)

        # Регистрируем кастомный representer
        yaml.add_representer(str, str_presenter)
        
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(
                new_config,
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
                width=float("inf"),
                indent=2
            )
        
        logger.info("Конфигурация успешно обновлена.")
        return {"message": "Конфигурация обновлена успешно"}
    except Exception as e:
        logger.error(f"Ошибка при обновлении конфигурации: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении конфигурации")
        

@app.post('/upload-files')
async def upload_file(file: UploadFile = File(...)):
    """Upload and index a file."""
    with TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, file.filename)
        logger.info(f"File saved to temp directory: {temp_path}")
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            logger.info("Start indexing...")
            indexing_service.run_indexing(data=temp_path)
            logger.info("End indexing!")
            return {"message": "File processed and indexed successfully."}
        except Exception as e:
            logger.error(f"Indexing failed: {str(e)}")
            return {"error": str(e)}

@app.post('/query', response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Handle RAG query request."""
    try:
        logger.info(f"Processing question: {request.question[:25]}...")
        result = pipeline.answer(request.question)
        logger.info(f'Successfully processed question')
        return result
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/')
async def root():
    """Root endpoint with API information."""
    return {
        "message": "RAG System API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload-files",
            "query": "/query"
        }
    }

@app.get('/health')
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "RAG API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 