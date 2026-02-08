#!/bin/bash
# Скрипт для восстановления production данных из бэкапа

set -e

if [ -z "$1" ]; then
  echo "❌ Ошибка: укажите имя бэкапа"
  echo "Использование: ./scripts/restore-prod.sh <backup_name>"
  echo ""
  echo "Доступные бэкапы:"
  ls -1 ./backups/ | grep "rag_backup_" | sed 's/_app_data.tar.gz//' | uniq
  exit 1
fi

BACKUP_DIR="./backups"
BACKUP_NAME=$1

echo "⚠️  ВНИМАНИЕ: Это удалит текущие данные и восстановит из бэкапа!"
echo "Бэкап: ${BACKUP_NAME}"
read -p "Продолжить? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
  echo "❌ Отменено"
  exit 0
fi

# Останавливаем контейнеры
echo "⏸️  Останавливаем контейнеры..."
docker-compose -f docker-compose.prod.yml down

# Удаляем старые volumes
echo "🗑️  Удаление старых volumes..."
docker volume rm rag_system_data rag_redis_data || true

# Создаем новые volumes
echo "📦 Создание новых volumes..."
docker volume create rag_system_data
docker volume create rag_redis_data

# Восстанавливаем app_data
echo "📥 Восстановление app_data..."
docker run --rm \
  -v rag_system_data:/data \
  -v $(pwd)/${BACKUP_DIR}:/backup \
  alpine sh -c "cd /data && tar xzf /backup/${BACKUP_NAME}_app_data.tar.gz --strip 1"

# Восстанавливаем Redis
echo "📥 Восстановление Redis..."
docker run --rm \
  -v rag_redis_data:/data \
  -v $(pwd)/${BACKUP_DIR}:/backup \
  alpine sh -c "cd /data && tar xzf /backup/${BACKUP_NAME}_redis.tar.gz --strip 1"

# Запускаем контейнеры
echo "▶️  Запускаем контейнеры..."
docker-compose -f docker-compose.prod.yml up -d

echo "✅ Восстановление завершено!"
echo "🔍 Проверьте работу системы: http://localhost:3000"
