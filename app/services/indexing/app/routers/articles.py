"""Articles management endpoints."""

import json
import os
from typing import List, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Path to articles JSON file
ARTICLES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    'data', 'articles.json'
)


class Article(BaseModel):
    """Article model."""
    id: int | None = None
    title: str
    description: str
    url: str
    tags: List[str] = []


def read_articles() -> List[Dict]:
    """Read articles from JSON file."""
    try:
        if os.path.exists(ARTICLES_FILE):
            with open(ARTICLES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create initial data if file doesn't exist
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
        raise HTTPException(status_code=500, detail=f"Ошибка чтения файла: {str(e)}")


def write_articles(articles: List[Dict]) -> None:
    """Write articles to JSON file."""
    try:
        os.makedirs(os.path.dirname(ARTICLES_FILE), exist_ok=True)
        with open(ARTICLES_FILE, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка записи в файл: {str(e)}")


@router.get("/articles", response_model=List[Article])
async def get_articles():
    """Get all articles."""
    return read_articles()


@router.post("/articles", response_model=Article)
async def add_article(article: Article):
    """Add a new article."""
    articles = read_articles()

    # Generate new ID
    if articles:
        new_id = max(a.get('id', 0) for a in articles) + 1
    else:
        new_id = 1

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
    """Delete an article by ID."""
    articles = read_articles()

    updated_articles = [a for a in articles if a.get('id') != article_id]

    if len(updated_articles) == len(articles):
        raise HTTPException(status_code=404, detail="Статья не найдена")

    write_articles(updated_articles)

    return {"message": "Статья успешно удалена", "id": article_id}


@router.put("/articles/{article_id}", response_model=Article)
async def update_article(article_id: int, article: Article):
    """Update an article by ID."""
    articles = read_articles()

    article_index = None
    for i, a in enumerate(articles):
        if a.get('id') == article_id:
            article_index = i
            break

    if article_index is None:
        raise HTTPException(status_code=404, detail="Статья не найдена")

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
