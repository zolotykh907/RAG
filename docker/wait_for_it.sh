#!/bin/bash
set -e

until curl -s http://ollama:11434/api/tags | grep -q "llama3"; do
  echo "Waiting llama3 ..."
  sleep 5
done
echo "Llama3 is ready."

until [ -f /app/data/RuBQ_index.index ]; do
  echo "Waiting FAISS index created..."
  sleep 10
done
echo "FAISS index is ready."

exec "$@"