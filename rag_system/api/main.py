from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rag_system.api import state
from rag_system.api.endpoints import config
from rag_system.api.endpoints import documents
from rag_system.api.endpoints import health
from rag_system.api.endpoints import query
from rag_system.api.endpoints import reload
from rag_system.api.endpoints import upload

state.initialize_services()

app = FastAPI(
    title="RAG System API",
    description="Unified API for document indexing and RAG querying",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router, tags=["query"])
app.include_router(upload.router, tags=["upload"])
app.include_router(config.router, tags=["config"])
app.include_router(health.router, tags=["health"])
app.include_router(reload.router, tags=["reload"])
app.include_router(documents.router, tags=["documents"])


def __getattr__(name: str) -> Any:
    """Proxy legacy module globals to api.state."""
    if hasattr(state, name):
        return getattr(state, name)
    raise AttributeError(name)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
