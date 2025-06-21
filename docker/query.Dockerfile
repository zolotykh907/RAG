FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY query/requirements.txt ./query/requirements.txt

RUN pip install --no-cache-dir -r query/requirements.txt

COPY query/ /app/query

EXPOSE 8000

CMD ["uvicorn", "query.app:app", "--host", "0.0.0.0", "--port", "8000"]