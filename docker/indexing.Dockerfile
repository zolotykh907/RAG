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
COPY app/ /docker_app/app/

CMD ["python", "-m", "app.indexing.run_indexing"]
