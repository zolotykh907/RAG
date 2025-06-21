FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY indexing/requirements.txt ./indexing/
RUN pip install --no-cache-dir -r indexing/requirements.txt

COPY indexing/ /app/indexing/

CMD ["python", "indexing/indexing.py"]
