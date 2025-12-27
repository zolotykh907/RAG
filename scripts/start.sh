#!/bin/bash

# Start microservices
echo "Starting RAG microservices..."
docker-compose -f docker-compose.microservices.yml up --build -d

echo ""
echo "Services started!"
echo "Gateway: http://localhost"
echo "Indexing: http://localhost:8001/docs"
echo "Query: http://localhost:8002/docs"
