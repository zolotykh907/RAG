#!/bin/bash
set -e

echo "Checking LM Studio availability..."
until curl -s http://localhost:1234/v1/models >/dev/null 2>&1; do
  echo "Waiting for LM Studio server on localhost:1234..."
  echo "Please ensure LM Studio is running with qwen/qwen3-4b-2507 model loaded."
  sleep 5
done
echo "LM Studio is ready."

until [ -f /app/data/RuBQ_index.index ]; do
  echo "Waiting FAISS index created..."
  sleep 10
done
echo "FAISS index is ready."

exec "$@"