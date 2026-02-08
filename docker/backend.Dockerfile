FROM python:3.10-slim

WORKDIR /docker_app

COPY pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir .

COPY rag_system/ /docker_app/rag_system/

EXPOSE 8000

CMD ["uvicorn", "rag_system.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
