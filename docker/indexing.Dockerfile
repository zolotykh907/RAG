FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-rus \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY indexing/requirements.txt ./indexing/requirements.txt

RUN pip install --no-cache-dir -r indexing/requirements.txt

COPY indexing/ /app/indexing/
COPY shared/ /app/shared/

CMD ["python", "indexing/run_indexing.py"]
