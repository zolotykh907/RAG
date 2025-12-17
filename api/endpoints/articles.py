import json
import os
from typing import List, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

router = APIRouter()

# Путь к JSON файлу со статьями (в папке data, которая монтируется в Docker)
ARTICLES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                              'data', 'articles.json')


class Article(BaseModel):
    id: int = None
    title: str
    description: str
    url: str
    tags: List[str] = []


def read_articles() -> List[Dict]:
    """Читает статьи из JSON файла."""
    try:
        print(f"[DEBUG] Checking articles file at: {ARTICLES_FILE}")
        print(f"[DEBUG] File exists: {os.path.exists(ARTICLES_FILE)}")

        if os.path.exists(ARTICLES_FILE):
            with open(ARTICLES_FILE, 'r', encoding='utf-8') as f:
                articles = json.load(f)
                print(f"[DEBUG] Loaded {len(articles)} articles")
                return articles
        else:
            print(f"[DEBUG] File not found, returning empty list")
            # Создаем файл с начальными данными, если его нет
            initial_articles = [
                {
                    "id": 1,
                    "title": "Введение в RAG-системы",
                    "description": "Основы Retrieval-Augmented Generation и их применение в современных AI-системах.",
                    "url": "https://arxiv.org/abs/2005.11401",
                    "tags": ["RAG", "NLP", "AI"]
                },
                {
                    "id": 2,
                    "title": "Векторные базы данных для RAG",
                    "description": "Сравнение различных векторных БД: FAISS, Pinecone, Milvus и Weaviate.",
                    "url": "https://www.pinecone.io/learn/vector-database/",
                    "tags": ["Векторные БД", "FAISS", "Embeddings"]
                }
            ]
            write_articles(initial_articles)
            return initial_articles
    except Exception as e:
        print(f"[DEBUG] Error reading articles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка чтения файла: {str(e)}")


def write_articles(articles: List[Dict]) -> None:
    """Записывает статьи в JSON файл."""
    try:
        os.makedirs(os.path.dirname(ARTICLES_FILE), exist_ok=True)
        with open(ARTICLES_FILE, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка записи в файл: {str(e)}")


@router.get("/articles", response_model=List[Article])
async def get_articles():
    """Получить все статьи."""
    articles = read_articles()
    return articles


@router.post("/articles", response_model=Article)
async def add_article(article: Article):
    """Добавить новую статью."""
    articles = read_articles()

    # Генерируем новый ID
    if articles:
        new_id = max(a.get('id', 0) for a in articles) + 1
    else:
        new_id = 1

    # Создаем новую статью
    new_article = {
        "id": new_id,
        "title": article.title,
        "description": article.description,
        "url": article.url,
        "tags": article.tags
    }

    articles.append(new_article)
    write_articles(articles)

    return new_article


@router.delete("/articles/{article_id}")
async def delete_article(article_id: int):
    """Удалить статью по ID."""
    articles = read_articles()

    # Находим и удаляем статью
    updated_articles = [a for a in articles if a.get('id') != article_id]

    if len(updated_articles) == len(articles):
        raise HTTPException(status_code=404, detail="Статья не найдена")

    write_articles(updated_articles)

    return {"message": "Статья успешно удалена", "id": article_id}


@router.put("/articles/{article_id}", response_model=Article)
async def update_article(article_id: int, article: Article):
    """Обновить статью по ID."""
    articles = read_articles()

    # Находим статью для обновления
    article_index = None
    for i, a in enumerate(articles):
        if a.get('id') == article_id:
            article_index = i
            break

    if article_index is None:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    # Обновляем статью
    updated_article = {
        "id": article_id,
        "title": article.title,
        "description": article.description,
        "url": article.url,
        "tags": article.tags
    }

    articles[article_index] = updated_article
    write_articles(articles)

    return updated_article
