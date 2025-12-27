FROM python:3.10-slim

LABEL maintainer="RAG Team"
LABEL service="indexing"
LABEL version="2.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY indexing/requirements.txt /app/indexing/requirements.txt
COPY query/requirements.txt /app/query/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r indexing/requirements.txt && \
    pip install --no-cache-dir -r query/requirements.txt && \
    pip install --no-cache-dir fastapi uvicorn python-multipart requests

# Copy application code
COPY shared/ /app/shared/
COPY indexing/ /app/indexing/
COPY query/ /app/query/
COPY api/config_manager.py /app/api/config_manager.py
COPY api/__init__.py /app/api/__init__.py
COPY services/indexing/app/ /app/app/

# Create necessary directories
RUN mkdir -p /app/data /app/logs /root/.cache/huggingface/hub

# Set Python path
ENV PYTHONPATH=/app:/app/shared:/app/indexing:/app/query:/app/api
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
