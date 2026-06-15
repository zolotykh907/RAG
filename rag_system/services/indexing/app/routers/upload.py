"""Upload endpoints for document processing and indexing."""

import asyncio
import os
import shutil
import uuid
import logging
import requests
from tempfile import TemporaryDirectory
from typing import Any, Dict

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile

from rag_system.indexing.indexing import Indexing
from rag_system.services.indexing.app import state
from rag_system.shared.data_loader import DataLoader

logger = logging.getLogger(__name__)
router: APIRouter = APIRouter()


def _safe_filename(filename: str) -> str:
    """Return a safe basename for an uploaded file."""
    base = os.path.basename(filename or "").strip().replace("\x00", "")
    if base in ("", ".", ".."):
        base = f"upload-{uuid.uuid4().hex}"
    return base


@router.post('/upload')
async def upload_file(
    file: UploadFile = File(...),
    indexing_service: Indexing = Depends(state.get_indexing_service),
    data_loader: DataLoader = Depends(state.get_data_loader),
) -> Dict[str, Any]:
    """Upload and index a file permanently.

    Args:
        file: The file to be uploaded and indexed.
        indexing_service: Injected indexing service.
        data_loader: Injected data loader.

    Returns:
        Confirmation message and indexing stats.

    Raises:
        HTTPException: If indexing fails.
    """
    with TemporaryDirectory() as temp_dir:
        safe_name = _safe_filename(file.filename or "upload")
        temp_path = os.path.join(temp_dir, safe_name)
        logger.info(f"Processing file: {file.filename}")

        loop = asyncio.get_running_loop()
        with open(temp_path, "wb") as f:
            await loop.run_in_executor(None, lambda: shutil.copyfileobj(file.file, f))

        try:
            logger.info("Starting indexing process...")
            await loop.run_in_executor(
                None, lambda: indexing_service.run_indexing(data=temp_path)
            )
            logger.info("Indexing completed successfully!")

            # Notify query service to reload index via internal HTTP call
            query_reloaded = False
            try:
                query_service_url = os.getenv('QUERY_SERVICE_URL', 'http://query:8002')
                response = requests.post(
                    f"{query_service_url}/api/query/reload",
                    timeout=5
                )
                query_reloaded = response.status_code == 200
                logger.info(f"Query service reload: {query_reloaded}")
            except Exception as e:
                logger.warning(f"Failed to notify query service: {str(e)}")

            return {
                "message": "File indexed successfully",
                "filename": file.filename,
                "query_service_reloaded": query_reloaded
            }

        except Exception as e:
            logger.error(f"Indexing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


@router.delete('/clear-index')
async def clear_index(
    indexing_service: Indexing = Depends(state.get_indexing_service),
) -> Dict[str, Any]:
    """Clear all indexed data.

    Args:
        indexing_service: Injected indexing service.

    Returns:
        Confirmation message.

    Raises:
        HTTPException: If the database is unavailable or clearing fails.
    """
    data_base = state.data_base
    if data_base is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        data_base.clear_index()
        indexing_service.clear_data()
        indexing_service.existing_hashes = []

        # Notify query service
        try:
            query_service_url = os.getenv('QUERY_SERVICE_URL', 'http://query:8002')
            requests.post(f"{query_service_url}/api/query/reset", timeout=5)
        except Exception as e:
            logger.warning(f"Failed to notify query service: {str(e)}")

        logger.info("Index cleared successfully")
        return {"message": "All indexed data cleared successfully"}

    except Exception as e:
        logger.error(f"Failed to clear index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
