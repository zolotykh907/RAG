FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /docker_app

# Copy project config and install dependencies
COPY pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir .

# Copy application code
COPY rag_system/ /docker_app/rag_system/

RUN mkdir -p /docker_app/data /docker_app/logs

EXPOSE 8000

CMD ["uvicorn", "rag_system.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
