FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-rus \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /docker_app

# Copy project config and install dependencies
COPY pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir .

# Copy application code
COPY rag_system/ /docker_app/rag_system/

CMD ["python", "-m", "rag_system.indexing.run_indexing"]
