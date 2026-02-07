FROM python:3.10-slim

LABEL maintainer="RAG Team"
LABEL service="indexing"
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
COPY app/ /docker_app/app/

# Create necessary directories
RUN mkdir -p /docker_app/data /docker_app/logs /root/.cache/huggingface/hub

ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the service
CMD ["uvicorn", "app.services.indexing.app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
