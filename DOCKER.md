# Docker Deployment Guide

Это руководство по запуску RAG системы в Docker.

## Архитектура

Система состоит из трех сервисов:

1. **Redis** - кэширование запросов
2. **API** (Backend) - единый API для индексации и запросов
3. **Frontend** - React приложение

## Требования

- Docker >= 20.10
- Docker Compose >= 2.0
- LM Studio (для локальной LLM) - должен быть запущен на хосте

## Быстрый старт

### 1. Запуск всех сервисов

```bash
docker-compose up -d
```

Это запустит:
- Redis на порту 6379
- API на порту 8000
- Frontend на порту 3000

### 2. Проверка статуса

```bash
docker-compose ps
```

### 3. Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f redis
```

### 4. Остановка

```bash
docker-compose down
```

## Переменные окружения

Вы можете настроить систему через переменные окружения в `docker-compose.yml`:

### API

- `LM_STUDIO_HOST` - URL к LM Studio (по умолчанию: `http://host.docker.internal:1234/v1`)
- `REDIS_HOST` - хост Redis (по умолчанию: `redis`)
- `REDIS_PORT` - порт Redis (по умолчанию: `6379`)
- `PYTHONUNBUFFERED` - отключение буферизации вывода Python

## Volumes (Тома)

Система использует следующие тома для постоянного хранения данных:

- `shared_data` - индексированные данные и FAISS индекс
- `model_cache` - кэш моделей HuggingFace
- `redis_data` - данные Redis
- `logs` - логи приложения

### Очистка данных

```bash
# Остановить и удалить контейнеры с данными
docker-compose down -v

# Или удалить конкретный том
docker volume rm rag_shared_data
```

## Доступ к сервисам

После запуска сервисы доступны по адресам:

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Redis: localhost:6379

## Разработка

### Пересборка образов

```bash
# Пересобрать все образы
docker-compose build

# Пересобрать конкретный сервис
docker-compose build api
docker-compose build frontend
```

### Запуск с пересборкой

```bash
docker-compose up -d --build
```

### Подключение к контейнеру

```bash
# API
docker exec -it rag_api bash

# Frontend
docker exec -it rag_frontend sh

# Redis
docker exec -it rag_redis redis-cli
```

## Production настройки

Для production рекомендуется:

1. **Использовать внешний Redis кластер**
   ```yaml
   environment:
     - REDIS_HOST=your-redis-host
     - REDIS_PORT=6379
   ```

2. **Настроить ресурсы**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
       reservations:
         cpus: '1'
         memory: 2G
   ```

3. **Добавить health checks**
   Уже настроены для всех сервисов

4. **Использовать secrets для конфигурации**
   ```yaml
   secrets:
     - lm_studio_api_key
   ```

5. **Настроить логирование**
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

## Troubleshooting

### API не может подключиться к LM Studio

Убедитесь, что LM Studio запущен на хосте и слушает на `0.0.0.0:1234`, а не только на `localhost`.

В настройках LM Studio:
- Settings → Network → Bind to: `0.0.0.0`

### Frontend не может подключиться к API

Проверьте, что:
1. API контейнер запущен: `docker ps | grep rag_api`
2. API доступен: `curl http://localhost:8000/health`
3. Nginx конфигурация правильная

### Redis connection refused

Проверьте:
```bash
docker logs rag_redis
docker exec -it rag_redis redis-cli ping
```

### Недостаточно памяти

Увеличьте лимиты Docker:
- Docker Desktop → Settings → Resources → Memory

## Мониторинг

### Использование ресурсов

```bash
docker stats
```

### Здоровье сервисов

```bash
# API
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000

# Redis
docker exec rag_redis redis-cli ping
```

## Обновление

```bash
# Остановить сервисы
docker-compose down

# Получить новый код
git pull

# Пересобрать и запустить
docker-compose up -d --build
```
