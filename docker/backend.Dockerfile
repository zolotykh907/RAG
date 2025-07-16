FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r indexing/requirements.txt
RUN pip install --no-cache-dir -r query/requirements.txt

EXPOSE 8000

CMD ["python", "app.py"]