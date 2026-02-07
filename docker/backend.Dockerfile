FROM python:3.10-slim

WORKDIR /docker_app

COPY pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir .

COPY app/ /docker_app/app/

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
