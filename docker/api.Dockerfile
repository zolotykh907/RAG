FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-rus \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY query/requirements.txt ./query/requirements.txt
COPY indexing/requirements.txt ./indexing/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r query/requirements.txt
RUN pip install --no-cache-dir -r indexing/requirements.txt

# Copy application code
COPY api/ /app/api/
COPY query/ /app/query/
COPY indexing/ /app/indexing/
COPY shared/ /app/shared/

# Create data directories
RUN mkdir -p /app/data /app/logs

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
