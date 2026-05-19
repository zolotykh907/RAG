# syntax=docker/dockerfile:1.7

FROM python:3.10-slim

LABEL maintainer="RAG Team"
LABEL service="indexing"
LABEL version="2.0.0"

# Set working directory
WORKDIR /docker_app

# Install system dependencies, including OCR tools for PDF/image ingestion.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-rus \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy project config and install dependencies
COPY pyproject.toml ./pyproject.toml
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install .

# Copy application code
COPY rag_system/ /docker_app/rag_system/

# Create necessary directories
RUN mkdir -p /docker_app/data /docker_app/logs /root/.cache/huggingface/hub

ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the service
CMD ["uvicorn", "rag_system.services.indexing.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
