# RAG Query System - Improved Version

Улучшенная система запросов для RAG (Retrieval-Augmented Generation) с поддержкой различных LLM моделей и оптимизированной архитектурой.

## 🚀 Основные улучшения

### ✅ Исправленные проблемы
- **Дублирование кода**: Удален дублирующий `data_base.py` и `logs.py`
- **Ошибки импортов**: Исправлены нестабильные относительные импорты
- **Обработка ошибок**: Добавлена комплексная обработка исключений
- **Валидация конфигурации**: Проверка обязательных полей конфигурации
- **Проблемы с логированием**: Исправлено дублирование логгеров

### 🆕 Новые возможности
- **CLI интерфейс**: Удобная командная строка с интерактивным режимом
- **Типизация**: Добавлены type hints для лучшей читаемости
- **Тесты**: Базовый набор unit-тестов
- **Статистика**: Мониторинг состояния системы
- **Гибкая конфигурация**: Поддержка пользовательских конфигураций

## 📁 Структура проекта

```
query/
├── config.py                 # Улучшенная конфигурация
├── config.yaml              # Файл конфигурации
├── query.py                 # Основной класс запросов (улучшен)
├── pipeline.py              # RAG пайплайн
├── llm.py                   # LLM интеграция (улучшена)
├── app.py                   # FastAPI приложение
├── run_query.py             # CLI интерфейс
├── requirements_improved.txt # Зависимости с версиями
├── test_query.py            # Тесты
└── README_QUERY.md          # Эта документация
```

## 🛠 Установка

1. **Установите зависимости**:
```bash
cd query
pip install -r requirements_improved.txt
```

2. **Установите Ollama** (для LLM):
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Скачайте с https://ollama.ai/download
```

3. **Запустите Ollama и скачайте модель**:
```bash
ollama serve
ollama pull llama3
```

## 🚀 Использование

### CLI интерфейс

```bash
# Интерактивный режим
python run_query.py

# Задать один вопрос
python run_query.py --question "Когда был основан ЦСКА?"

# Показать статус системы
python run_query.py --status

# Использовать пользовательскую конфигурацию
python run_query.py --config my_config.yaml --question "Ваш вопрос"

# Изменить количество релевантных документов
python run_query.py --k 10 --question "Ваш вопрос"

# Подробное логирование
python run_query.py --verbose
```

### API интерфейс

```bash
# Запуск API сервера
uvicorn app:app --host 0.0.0.0 --port 8000

# Тестирование API
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "Когда был основан ЦСКА?"}'
```

### Программное использование

```python
from config import Config
from query import Query
from pipeline import RAGPipeline
from llm import LLMResponder
from indexing.data_base import FaissDB

# Инициализация
config = Config('config.yaml')
data_base = FaissDB(config)
query_service = Query(config, data_base)
responder = LLMResponder(config)
pipeline = RAGPipeline(config, query_service, responder)

# Запрос
result = pipeline.answer("Когда был основан ЦСКА?")
print(f"Ответ: {result['answer']}")
print(f"Релевантные документы: {len(result['texts'])}")
```

## ⚙️ Конфигурация

### config.yaml

```yaml
data:
  index_path: "./data/RuBQ_index.index"
  logs_dir: './logs'
  processed_data_path: "./data/processed_data.json"

models:
  emb_model_name: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
  llm: "llama3"
  prompt_template: |
    Ты - интеллектуальный помощник, который отвечает только на основе предоставленного контекста из базы знаний. Никогда не используй свои собственные знания.

    Вопрос: {question}

    Контекст:
    {context}

    Инструкции:
    1. Если ответ содержится в контексте - дай точный ответ, процитировав или перефразировав соответствующую часть контекста.
    2. Если в контексте нет информации для ответа - строго скажи только: "Информация не найдена в базе знаний".
    3. Никогда не дополняй ответ информацией не из контекста.
    4. Всегда отвечай на русском языке.

rag:
  k: 5

api:
  endpoint: "/query"
  title: "RAG Query API"
  host: "0.0.0.0"
  port: 8000
  ollama_host: "http://localhost:11434"
```

### Переменные окружения

```bash
export OLLAMA_HOST="http://localhost:11434"
export RAG_LOGS_DIR="/path/to/logs"
export RAG_INDEX_PATH="/path/to/index"
```

## 🧪 Тестирование

```bash
# Установить тестовые зависимости
pip install pytest pytest-asyncio httpx

# Запустить тесты
pytest test_query.py -v

# Запустить с покрытием
pytest test_query.py --cov=. --cov-report=html
```

## 📊 Мониторинг

### Логи

Логи сохраняются в директории `logs/`:
- `QueryRunner.log` - лог CLI интерфейса
- `QueryService.log` - лог сервиса запросов
- `RAG_LLM.log` - лог LLM интеграции
- `RAGPipeline.log` - лог RAG пайплайна
- `RAG_API.log` - лог API сервера

### Статистика

```bash
python run_query.py --status
```

Вывод:
```
=== RAG Query System Status ===
Index path: ./data/RuBQ_index.index
Data path: ./data/processed_data.json
Embedding model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
LLM model: llama3
Ollama host: http://localhost:11434
Number of texts loaded: 61956
FAISS index vectors: 61956
Retrieval parameter k: 5
```

## 🔧 Поддерживаемые LLM модели

### Ollama модели
- `llama3` - Llama 3 (рекомендуется)
- `llama2` - Llama 2
- `mistral` - Mistral
- `codellama` - Code Llama
- `qwen` - Qwen

### Настройка новой модели

1. Скачайте модель:
```bash
ollama pull your-model-name
```

2. Обновите конфигурацию:
```yaml
models:
  llm: "your-model-name"
```

## 🚨 Обработка ошибок

Система включает комплексную обработку ошибок:

- **Валидация входных данных**
- **Проверка существования файлов**
- **Обработка сетевых ошибок**
- **Graceful degradation при сбоях LLM**
- **Автоматическое восстановление соединений**

## 📈 Производительность

### Оптимизации
- **Кэширование** эмбеддингов
- **Batch processing** для больших запросов
- **Асинхронная обработка** в API
- **Эффективный поиск** в FAISS

### Рекомендации
- Используйте SSD для хранения индекса
- Настройте `k` в зависимости от типа вопросов
- Используйте более мощные LLM модели для лучших ответов
- Мониторьте использование памяти

## 🔄 Интеграция с indexing

Query система автоматически использует данные, созданные системой индексации:

1. **Индекс FAISS** - для быстрого поиска
2. **Обработанные тексты** - для контекста
3. **Модель эмбеддингов** - для векторизации запросов

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Добавьте тесты для новой функциональности
4. Убедитесь, что все тесты проходят
5. Создайте Pull Request

## 📝 Лицензия

MIT License

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи в `logs/`
2. Убедитесь в корректности конфигурации
3. Проверьте, что Ollama запущен и модель скачана
4. Убедитесь, что индекс создан системой индексации
5. Создайте issue с подробным описанием проблемы

## 🔗 Полезные ссылки

- [Ollama документация](https://ollama.ai/docs)
- [FastAPI документация](https://fastapi.tiangolo.com/)
- [LangChain документация](https://python.langchain.com/)
- [FAISS документация](https://faiss.ai/) 