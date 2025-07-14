FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY query/requirements.txt ./query/requirements.txt

RUN pip install --no-cache-dir -r query/requirements.txt

COPY query/ /app/query
COPY shared/ /app/shared/
COPY static/ /app/static/
COPY docker/wait_for_it.sh /app/wait_for_it.sh
RUN chmod +x /app/wait_for_it.sh

EXPOSE 8000

CMD ["/app/wait_for_it.sh","uvicorn", "query.app:app", "--host", "0.0.0.0", "--port", "8000"]