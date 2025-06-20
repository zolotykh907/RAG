# Используем официальный образ Python
FROM python:3.10-slim

# Установка системных зависимостей (если нужно)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создаём рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY indexing/requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код из папки indexing
COPY indexing/ /app/

# Точка входа (запуск скрипта)
CMD ["python", "indexing.py"]
