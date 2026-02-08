FROM python:3.10-slim

LABEL maintainer="RAG Team"
LABEL service="query"
LABEL version="2.0.0"

# Set working directory
WORKDIR /docker_app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project config and install dependencies
COPY pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir .

# Copy application code
COPY rag_system/ /docker_app/rag_system/

# Create necessary directories
RUN mkdir -p /docker_app/data /docker_app/logs /root/.cache/huggingface/hub

ENV PYTHONUNBUFFERED=1

# Environment variables for LM Studio
ENV LM_STUDIO_HOST=http://host.docker.internal:1234/v1

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the service
CMD ["uvicorn", "rag_system.services.query.app.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]
