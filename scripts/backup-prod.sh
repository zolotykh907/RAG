#!/bin/bash
# Скрипт для бэкапа production данных

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="rag_backup_${TIMESTAMP}"

echo "🔄 Создание бэкапа production данных..."

# Создаем папку для бэкапов
mkdir -p ${BACKUP_DIR}

# Останавливаем API для консистентности данных
echo "⏸️  Останавливаем API контейнер..."
docker-compose -f docker-compose.prod.yml stop api

# Бэкап app_data (статьи, документы, индексы)
echo "📦 Создание бэкапа app_data..."
docker run --rm \
  -v rag_app_data:/data \
  -v $(pwd)/${BACKUP_DIR}:/backup \
  alpine tar czf /backup/${BACKUP_NAME}_app_data.tar.gz /data

# Бэкап Redis
echo "📦 Создание бэкапа Redis..."
docker run --rm \
  -v rag_redis_data:/data \
  -v $(pwd)/${BACKUP_DIR}:/backup \
  alpine tar czf /backup/${BACKUP_NAME}_redis.tar.gz /data

# Бэкап логов (опционально)
echo "📦 Создание бэкапа логов..."
docker run --rm \
  -v rag_logs:/data \
  -v $(pwd)/${BACKUP_DIR}:/backup \
  alpine tar czf /backup/${BACKUP_NAME}_logs.tar.gz /data

# Запускаем API обратно
echo "▶️  Запускаем API контейнер..."
docker-compose -f docker-compose.prod.yml start api

echo "✅ Бэкап завершен!"
echo "📂 Файлы бэкапа:"
ls -lh ${BACKUP_DIR}/${BACKUP_NAME}*

echo ""
echo "📝 Для восстановления используйте: ./scripts/restore-prod.sh ${BACKUP_NAME}"
