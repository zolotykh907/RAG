import json
import logging
import os
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Path to articles JSON file (in data/ directory, mounted in Docker)
ARTICLES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                              'data', 'articles.json')


class Article(BaseModel):
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
                articles = json.load(f)
                logger.debug(f"Loaded {len(articles)} articles")
                return articles
        else:
            logger.info("Articles file not found, creating with initial data")
            initial_articles = [
                {
                    "id": 1,
                    "title": "Introduction to RAG systems",
                    "description": "Basics of Retrieval-Augmented Generation and their application in modern AI systems.",
                    "url": "https://arxiv.org/abs/2005.11401",
                    "tags": ["RAG", "NLP", "AI"]
                },
                {
                    "id": 2,
                    "title": "Vector databases for RAG",
                    "description": "Comparison of vector DBs: FAISS, Pinecone, Milvus and Weaviate.",
                    "url": "https://www.pinecone.io/learn/vector-database/",
                    "tags": ["Vector DB", "FAISS", "Embeddings"]
                }
            ]
            write_articles(initial_articles)
            return initial_articles
    except Exception as e:
        logger.error(f"Error reading articles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading articles file: {str(e)}")


def write_articles(articles: List[Dict]) -> None:
    """Write articles to JSON file."""
    try:
        os.makedirs(os.path.dirname(ARTICLES_FILE), exist_ok=True)
        with open(ARTICLES_FILE, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing articles file: {str(e)}")


@router.get("/articles", response_model=List[Article])
async def get_articles():
    """Get all articles."""
    articles = read_articles()
    return articles


@router.post("/articles", response_model=Article)
async def add_article(article: Article):
    """Add a new article."""
    articles = read_articles()

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
        raise HTTPException(status_code=404, detail="Article not found")

    write_articles(updated_articles)

    return {"message": "Article deleted successfully", "id": article_id}


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
        raise HTTPException(status_code=404, detail="Article not found")

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
