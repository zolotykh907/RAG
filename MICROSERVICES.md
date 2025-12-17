# Микросервисная архитектура RAG - Быстрый старт

## Запуск микросервисов

### 1. Собрать frontend

```bash
cd react_frontend
npm install
npm run build
cd ..
```

### 2. Запустить все сервисы

```bash
docker-compose -f docker-compose.microservices.yml up -d --build
```

### 3. Проверить статус

```bash
docker-compose -f docker-compose.microservices.yml ps
```

### 4. Проверить health

```bash
# Gateway
curl http://localhost/health

# Indexing service
curl http://localhost/health/indexing

# Query service
curl http://localhost/health/query
```

## Доступ к сервисам

- **Frontend**: http://localhost или http://localhost:3000
- **API Gateway**: http://localhost
- **Indexing Service** (прямой доступ): http://localhost:8001
- **Query Service** (прямой доступ): http://localhost:8002
- **Swagger Indexing**: http://localhost:8001/docs
- **Swagger Query**: http://localhost:8002/docs

## Основные команды

### Логи

```bash
# Все сервисы
docker-compose -f docker-compose.microservices.yml logs -f

# Конкретный сервис
docker-compose -f docker-compose.microservices.yml logs -f indexing
docker-compose -f docker-compose.microservices.yml logs -f query
docker-compose -f docker-compose.microservices.yml logs -f gateway
```

### Перезапуск

```bash
# Все сервисы
docker-compose -f docker-compose.microservices.yml restart

# Конкретный сервис
docker-compose -f docker-compose.microservices.yml restart indexing
docker-compose -f docker-compose.microservices.yml restart query
```

### Остановка

```bash
docker-compose -f docker-compose.microservices.yml down
```

### Полная очистка (с удалением данных)

```bash
docker-compose -f docker-compose.microservices.yml down -v
```

## Горизонтальное масштабирование

### Увеличить количество экземпляров Query Service

```bash
docker-compose -f docker-compose.microservices.yml up -d --scale query=3
```

### Увеличить количество экземпляров Indexing Service

```bash
docker-compose -f docker-compose.microservices.yml up -d --scale indexing=2
```

## Мониторинг

### Статистика ресурсов

```bash
docker stats
```

### Логи в реальном времени

```bash
docker-compose -f docker-compose.microservices.yml logs -f --tail=100
```

## Архитектура

Подробная документация: [ARCHITECTURE.md](ARCHITECTURE.md)

### Краткая схема:

```
Client (Browser)
       ↓
API Gateway (Nginx) :80
       ↓
       ├─→ Indexing Service :8001
       │   ├─ Upload documents
       │   ├─ Manage documents
       │   └─ Articles API
       │
       └─→ Query Service :8002
           ├─ RAG queries
           ├─ Temp sessions
           └─ Search

Redis :6379 (cache & sessions)
FAISS Index (shared volume)
LM Studio (external LLM)
```

## Преимущества микросервисной архитектуры

✅ **Независимое масштабирование** - можно масштабировать Query Service (больше запросов) отдельно от Indexing Service

✅ **Изоляция сбоев** - если упадет Indexing, Query продолжит работать

✅ **Независимое развертывание** - можно обновлять сервисы по отдельности

✅ **Оптимизация ресурсов** - разные лимиты памяти для разных сервисов

✅ **Rate limiting** - защита от перегрузки через Nginx

## Миграция со старого docker-compose.yml

Старый монолит остался в `docker-compose.yml`, новая архитектура в `docker-compose.microservices.yml`.

Чтобы переключиться:

```bash
# Остановить старую версию
docker-compose down

# Запустить новую версию
docker-compose -f docker-compose.microservices.yml up -d --build
```

Данные совместимы, т.к. используются те же volumes.
