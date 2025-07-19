#!/usr/bin/env python3
"""
RAG System API Runner
Запускает FastAPI приложение из модуля api
"""

import uvicorn
from api.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 