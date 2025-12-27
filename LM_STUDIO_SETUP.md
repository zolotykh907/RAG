# Настройка LM Studio для RAG системы

### 1. Установка LM Studio

1. Скачайте LM Studio с официального сайта: https://lmstudio.ai/
2. Установите приложение для вашей операционной системы (Windows, macOS, Linux)

### 2. Загрузка модели Qwen 3

1. Откройте LM Studio
2. Найдите модель `qwen3-4b-2507`
3. Нажмите "Download"
4. Дождитесь завершения загрузки

### 3. Запуск локального сервера

1. Перейдите на вкладку "Local Server" (Локальный сервер)
2. В разделе "Select a model to load" выберите загруженную модель Qwen
3. Настройте параметры (опционально):
   - **Context Length**: 4096 или больше
   - **GPU Offload**: максимальное значение для вашей системы
   - **Temperature**: 0.7 (по умолчанию в коде)
4. Нажмите кнопку "Start Server"
5. Убедитесь, что сервер запущен на порту **1234** (по умолчанию)
6. В интерфейсе должно появиться сообщение: "Server is running on http://localhost:1234"

### 4. Проверка работы сервера

Откройте терминал и выполните команду:

```bash
curl http://localhost:1234/v1/models
```

Вы должны увидеть JSON-ответ с информацией о загруженной модели.

### 5. Запуск RAG системы

После того как LM Studio запущен и модель загружена:

**Локальный запуск:**
```bash
# Убедитесь, что зависимости установлены
pip install -r query/requirements.txt

# Запустите API сервер
python run_api.py

# В другом терминале запустите frontend
python run_frontend.py
```

**Docker запуск:**
```bash
docker-compose up --build
```

**Важно:** Docker контейнер использует `network_mode: "host"`, чтобы получить доступ к LM Studio на localhost:1234.

## Переменные окружения

Вы можете настроить адрес LM Studio через переменную окружения:

```bash
export LM_STUDIO_HOST=http://localhost:1234/v1
```

Или изменить в файле `query/config.yaml`:

```yaml
api:
  lm_studio_host: http://localhost:1234/v1
```

## Альтернативные модели

Вы можете использовать другие модели из LM Studio. Просто:

1. Загрузите нужную модель в LM Studio
2. Запустите её в Local Server
3. Обновите название модели в `query/config.yaml`:

```yaml
models:
  llm: your-model-name
```
