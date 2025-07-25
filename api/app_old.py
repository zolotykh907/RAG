import sys
import os
import shutil
from tempfile import TemporaryDirectory
from typing import Dict, List
import uuid
import numpy as np
import pandas as pd
import faiss
from langchain_text_splitters import RecursiveCharacterTextSplitter

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shared'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'indexing'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'query'))

from logs import setup_logging
from my_config import Config as SharedConfig
from data_loader import DataLoader
from data_base import FaissDB, ChromaDB
from data_processing import normalize_text

from indexing import Indexing

from query.query import Query
from query.pipeline import RAGPipeline
from query.llm import LLMResponder

import yaml
from fastapi.responses import JSONResponse

shared_config = SharedConfig('indexing/config.yaml')
query_config = SharedConfig('query/config.yaml')

logger = setup_logging(shared_config.logs_dir, 'RAG_APP')

temp_indexes: Dict[str, List] = {}

data_loader = None
data_base = None
indexing_service = None
query_service = None
responder = None
pipeline = None

try:
    data_loader = DataLoader(shared_config)
    data_base = FaissDB(shared_config)
    indexing_service = Indexing(shared_config, data_loader, data_base)
    
    # Инициализируем query_service с обработкой ошибок
    try:
        query_service = Query(query_config, data_base)
        logger.info('Query service initialized successfully.')
    except Exception as e:
        logger.warning(f'Failed to initialize Query service (index may not exist): {str(e)}')
        query_service = None
    
    # Инициализируем responder
    try:
        responder = LLMResponder(query_config)
        logger.info('LLM responder initialized successfully.')
    except Exception as e:
        logger.error(f'Failed to initialize LLM responder: {str(e)}')
        raise
    
    # Инициализируем pipeline только если query_service доступен
    if query_service is not None:
        pipeline = RAGPipeline(config=query_config, query=query_service, responder=responder)
        logger.info('RAG pipeline initialized successfully.')
    else:
        logger.warning('RAG pipeline not initialized - no index available.')
    
    logger.info('RAG API initialized successfully.')
except Exception as e:
    logger.error(f'Failed to initialize RAG API: {str(e)}')

    logger.warning('Continuing with limited functionality...')

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
    session_id: str = None

class QueryResponse(BaseModel):
    """Response model for RAG query endpoint."""
    answer: str
    texts: list

def get_config_path(service: str) -> str:
    """Возвращает путь к конфигурационному файлу в зависимости от сервиса."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, service, 'config.yaml')

def process_file_temp(file_path: str) -> List:
    """Обработать файл и создать эмбеддинги без сохранения на диск."""
    try:
        # Загружаем данные из файла
        df = data_loader.load_data(file_path)
        
        # Нормализуем текст
        df['text'] = df['text'].apply(lambda x: normalize_text(x) if pd.notna(x) else '')
        
        # Разбиваем на чанки
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        chunks = []
        for text in df['text']:
            if text.strip():
                chunks.extend(text_splitter.split_text(text))
        
        # Создаем эмбеддинги
        embeddings = indexing_service.emb_model.encode(chunks, show_progress_bar=True)
        
        # Сохраняем чанки и эмбеддинги в памяти
        temp_data = {
            'chunks': chunks,
            'embeddings': embeddings.tolist()
        }
        
        logger.info(f"Temporary indexing completed. Created {len(chunks)} chunks with embeddings.")
        return temp_data
        
    except Exception as e:
        logger.error(f"Temporary indexing failed: {str(e)}")
        raise

@app.post('/upload-temp')
async def upload_temp_file(file: UploadFile = File(...)):
    """Upload and temporarily index a file for session use."""
    if indexing_service is None:
        raise HTTPException(
            status_code=503, 
            detail="Indexing service not available. Please check configuration and try again."
        )
   
    try:
        session_id = str(uuid.uuid4())
        
        with TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, file.filename)
            logger.info(f"Temporary file saved: {temp_path}")
            
            with open(temp_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
 
            temp_data = process_file_temp(temp_path)
            
            temp_indexes[session_id] = temp_data
            
            logger.info(f"Temporary file indexed successfully. Session ID: {session_id}")
            return {
                "message": "File processed and temporarily indexed successfully.",
                "session_id": session_id,
                "chunks_count": len(temp_data['chunks'])
            }
            
    except Exception as e:
        logger.error(f"Temporary indexing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete('/clear-temp/{session_id}')
async def clear_temp_session(session_id: str):
    """Clear temporary session data."""
    try:
        if session_id in temp_indexes:
            del temp_indexes[session_id]
            logger.info(f"Temporary session {session_id} cleared")
            return {"message": "Session cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        logger.error(f"Failed to clear session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config(service: str):
    """Получить текущую конфигурацию для указанного сервиса."""
    config_path = get_config_path(service)
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail=f"Конфигурационный файл для {service} не найден")
    
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        return config_data
    except Exception as e:
        logger.error(f"Не удалось прочитать конфигурацию для {service}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при чтении конфигурации")

from fastapi import Body


@app.post("/config")
async def update_config(service: str, new_config: Dict = Body(...)):
    """Обновить конфигурацию для указанного сервиса."""
    config_path = get_config_path(service)
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail=f"Конфигурационный файл для {service} не найден")
    
    try:
        def str_presenter(dumper, data):
            if '\n' in data:
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data)

        yaml.add_representer(str, str_presenter)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                new_config,
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
                width=float("inf"),
                indent=2
            )
        
        logger.info(f"Конфигурация для {service} успешно обновлена.")
        return {"message": f"Конфигурация для {service} обновлена успешно"}
    except Exception as e:
        logger.error(f"Ошибка при обновлении конфигурации для {service}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении конфигурации")


@app.post('/upload-files')
async def upload_file(file: UploadFile = File(...)):
    """Upload and index a file."""
    if indexing_service is None:
        raise HTTPException(
            status_code=503, 
            detail="Indexing service not available. Please check configuration and try again."
        )
   
    with TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, file.filename)
        logger.info(f"File saved to temp directory: {temp_path}")
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            logger.info("Start indexing...")
            indexing_service.run_indexing(data=temp_path)
            logger.info("End indexing!")
           
            global query_service, pipeline
            try:
                query_service = Query(query_config, data_base)
                pipeline = RAGPipeline(config=query_config, query=query_service, responder=responder)
                logger.info('Query service and pipeline reinitialized after indexing.')
            except Exception as e:
                logger.warning(f'Failed to reinitialize query service after indexing: {str(e)}')
           
            return {"message": "File processed and indexed successfully."}
        except Exception as e:
            logger.error(f"Indexing failed: {str(e)}")
            return {"error": str(e)}

@app.post('/query', response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Handle RAG query request."""
    try:
        logger.info(f"Processing question: {request.question[:25]}...")
        
        if request.session_id and request.session_id in temp_indexes:
            session_id = request.session_id
            temp_data = temp_indexes[session_id]
            temp_chunks = temp_data['chunks']
            temp_embeddings = np.array(temp_data['embeddings'])
            
            class CombinedQueryService:
                def __init__(self, permanent_query, temp_index, temp_chunks, emb_model, k=5):
                    self.permanent_query = permanent_query
                    self.temp_index = temp_index
                    self.temp_chunks = temp_chunks
                    self.emb_model = emb_model
                    self.k = k
                
                def query(self, question):
                    results = []
                    
                    if self.permanent_query is not None:
                        try:
                            permanent_results = self.permanent_query.query(question)
                            results.extend(permanent_results)
                        except Exception as e:
                            logger.warning(f"Failed to search in permanent index: {e}")
                    
                    try:
                        query_embedding = self.emb_model.encode([question])
                        D, I = self.temp_index.search(query_embedding.astype('float32'), k=min(self.k, len(self.temp_chunks)))
                        
                        temp_results = []
                        for i in I[0]:
                            if i < len(self.temp_chunks):
                                temp_results.append(self.temp_chunks[i])
                            else:
                                logger.warning(f"Temporary index returned invalid index {i} (max: {len(self.temp_chunks)-1})")
                        
                        results.extend(temp_results)
                    except Exception as e:
                        logger.warning(f"Failed to search in temporary index: {e}")
                    
                    unique_results = list(dict.fromkeys(results))  
                    return unique_results[:self.k * 2]  

            temp_index = faiss.IndexFlatIP(temp_embeddings.shape[1])
            temp_index.add(temp_embeddings.astype('float32'))
            
            combined_query_service = CombinedQueryService(
                query_service,  
                temp_index,    
                temp_chunks,    
                indexing_service.emb_model,  
                k=5  
            )
            
            combined_pipeline = RAGPipeline(config=query_config, query=combined_query_service, responder=responder)
            
            result = combined_pipeline.answer(request.question)
            
            logger.info(f"Combined query processed successfully for session {session_id}")
            return QueryResponse(answer=result['answer'], texts=result['texts'])
        else:
            if pipeline is None:
                return QueryResponse(
                    answer="Индекс не загружен или не существует. Пожалуйста, загрузите и проиндексируйте файлы через вкладку 'Upload', или прикрепите временный файл через кнопку скрепки в чате.",
                    texts=[]
                )
            else:
                result = pipeline.answer(request.question)
                logger.info(f'Successfully processed question')
                return result
         
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reload")
async def reload_pipeline(service: str):
    global query_config, shared_config, data_base, query_service, responder, pipeline, data_loader, indexing_service

    try:
        query_config.reload()
        shared_config.reload()
        if service == "query":
            data_base = FaissDB(shared_config)
           
            try:
                query_service = Query(query_config, data_base)
                pipeline = RAGPipeline(config=query_config, query=query_service, responder=responder)
                logger.info('Query service and pipeline reinitialized successfully.')
            except Exception as e:
                logger.warning(f'Failed to reinitialize Query service: {str(e)}')
                query_service = None
                pipeline = None
        elif service == "indexing":
            data_loader = DataLoader(shared_config)
            data_base = FaissDB(shared_config)
            indexing_service = Indexing(shared_config, data_loader, data_base)
        else:
            raise ValueError("Неизвестный сервис")

        logger.info(f"{service} конфигурация перезагружена")
        return {"message": f"{service} конфигурация перезагружена успешно"}
    except Exception as e:
        logger.error(f"Ошибка при перезагрузке: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/')
async def root():
    """Root endpoint with API information."""
    return {
        "message": "RAG System API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload-files",
            "query": "/query",
            "config": "/config?service={query|indexing}"
        }
    }

@app.get('/health')
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "RAG API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)