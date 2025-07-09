import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

def test_faiss_index(index_path: str, test_query: str = "пример запроса"):
    """
    Тестирует загрузку FAISS индекса и выполняет пробный поиск.
    
    Args:
        index_path: Путь к файлу индекса FAISS
        test_query: Тестовый запрос для поиска
    """
    try:
        # 1. Загрузка индекса
        print(f"⏳ Загружаем индекс из {index_path}...")
        index = faiss.read_index(index_path)
        print(f"✅ Индекс загружен. Количество векторов: {index.ntotal}")
        
        # 2. Проверка размерности
        dim = index.d
        print(f"📏 Размерность векторов: {dim}")
        
        # 3. Создание тестового эмбеддинга
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")  # Такая же модель, как при создании индекса
        query_embedding = model.encode([test_query], normalize_embeddings=True)
        query_embedding = np.array(query_embedding, dtype=np.float32)
        
        # 4. Поиск в индексе
        k = 3  # Количество ближайших соседей
        distances, indices = index.search(query_embedding, k)
        
        print("\n🔍 Результаты поиска:")
        print(f"Запрос: '{test_query}'")
        print(f"Найденные индексы: {indices[0]}")
        print(f"Дистанции: {distances[0]}")
        
        # 5. Проверка качества (демо)
        if index.ntotal > 0 and indices[0][0] >= 0:
            print("\n🟢 Индекс работает корректно")
        else:
            print("\n🟡 Внимание: индекс пуст или поиск не дал результатов")
            
    except Exception as e:
        print(f"\n🔴 Ошибка при тестировании индекса: {str(e)}")

# Пример использования
if __name__ == "__main__":
    # Укажите путь к вашему индексу
    test_faiss_index(
        index_path="data/RuBQ_index.index",
        test_query="Когда основан ЦСКА"  # Тестовый запрос
    )