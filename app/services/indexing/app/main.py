"""
Indexing Service - Handles document upload, processing, and indexing.

Responsibilities:
- Document upload and validation
- Text extraction and chunking
- Embedding generation
- Index creation and updates
- Document management (CRUD)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Optional

from app.shared.logs import setup_logging
from app.shared.my_config import Config as SharedConfig
from app.shared.data_loader import DataLoader
from app.shared.data_base import FaissDB
from app.indexing import Indexing

# Configuration
shared_config: Any = SharedConfig('app/indexing/config.yaml')
logger = setup_logging(shared_config.logs_dir, 'INDEXING_SERVICE')

# Global services
data_loader: Optional[DataLoader] = None
data_base: Optional[FaissDB] = None
indexing_service: Optional[Indexing] = None


def initialize_services():
    """Initialize indexing services with error handling."""
    global data_loader, data_base, indexing_service

    try:
        data_loader = DataLoader(shared_config)
        data_base = FaissDB(shared_config)
        indexing_service = Indexing(shared_config, data_loader, data_base)

        logger.info('Indexing service initialized successfully.')
    except Exception as e:
        logger.error(f'Failed to initialize Indexing service: {str(e)}')
        raise


initialize_services()

# FastAPI app
app = FastAPI(
    title="RAG Indexing Service",
    description="Microservice for document indexing and embedding generation",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Gateway will handle CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection
def get_indexing_service() -> Indexing:
    """Get indexing service instance."""
    if indexing_service is None:
        raise HTTPException(
            status_code=503,
            detail="Indexing service not available"
        )
    return indexing_service


def get_data_loader() -> DataLoader:
    """Get data loader instance."""
    if data_loader is None:
        raise HTTPException(
            status_code=503,
            detail="Data loader not available"
        )
    return data_loader


def get_data_base() -> FaissDB:
    """Get database instance."""
    if data_base is None:
        raise HTTPException(
            status_code=503,
            detail="Database not available"
        )
    return data_base


# Import routers after app initialization to avoid circular imports
from app.routers import upload, documents, health, articles, config, reload

app.include_router(upload.router, prefix="/api/indexing", tags=["upload"])
app.include_router(documents.router, prefix="/api/indexing", tags=["documents"])
app.include_router(articles.router, prefix="/api/indexing", tags=["articles"])
app.include_router(config.router, prefix="/api/indexing", tags=["config"])
app.include_router(reload.router, prefix="/api/indexing", tags=["reload"])
app.include_router(health.router, tags=["health"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "RAG Indexing Service",
        "version": "2.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
