import numpy as np
import pandas as pd
import faiss
import logging
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

from query.pipeline import RAGPipeline

logger = logging.getLogger(__name__)


class CombinedQueryService:
    """Combined query service that searches both permanent and temporary indexes."""
    
    def __init__(self, permanent_query, temp_index, temp_chunks, emb_model, k=5):
        self.permanent_query = permanent_query
        self.temp_index = temp_index
        self.temp_chunks = temp_chunks
        self.emb_model = emb_model
        self.k = k
    
    def query(self, question):
        """Search in both permanent and temporary indexes."""
        results = []
        
        # Ищем в постоянном индексе (если доступен)
        if self.permanent_query is not None:
            try:
                permanent_results = self.permanent_query.query(question)
                results.extend(permanent_results)
            except Exception as e:
                logger.warning(f"Failed to search in permanent index: {e}")
        
        # Ищем во временном индексе
        try:
            query_embedding = self.emb_model.encode([question])
            D, I = self.temp_index.search(query_embedding.astype('float32'), k=min(self.k, len(self.temp_chunks)))
            
            # Получаем релевантные тексты из временного индекса
            temp_results = []
            for i in I[0]:
                if i < len(self.temp_chunks):
                    temp_results.append(self.temp_chunks[i])
                else:
                    logger.warning(f"Temporary index returned invalid index {i} (max: {len(self.temp_chunks)-1})")
            
            results.extend(temp_results)
        except Exception as e:
            logger.warning(f"Failed to search in temporary index: {e}")
        
        # Убираем дубликаты и ограничиваем количество результатов
        unique_results = list(dict.fromkeys(results))  # Сохраняет порядок
        return unique_results[:self.k * 2]  # Возвращаем больше результатов, так как объединили два источника


def process_file_temp(file_path: str, data_loader, indexing_service) -> List:
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


def create_combined_pipeline(query_service, temp_data, indexing_service, query_config, responder):
    """Create a combined pipeline for temporary and permanent data."""
    temp_chunks = temp_data['chunks']
    temp_embeddings = np.array(temp_data['embeddings'])
    
    # Создаем временный FAISS индекс для временных данных
    temp_index = faiss.IndexFlatIP(temp_embeddings.shape[1])
    temp_index.add(temp_embeddings.astype('float32'))
    
    # Создаем объединенный query сервис
    combined_query_service = CombinedQueryService(
        query_service,  # постоянный query сервис (может быть None)
        temp_index,     # временный FAISS индекс
        temp_chunks,    # временные чанки
        indexing_service.emb_model,  # модель эмбеддингов
        k=5  # количество результатов из каждого источника
    )
    
    # Создаем объединенный pipeline
    combined_pipeline = RAGPipeline(config=query_config, query=combined_query_service, responder=responder)
    
    return combined_pipeline


# Импорт для функции normalize_text
from data_processing import normalize_text 