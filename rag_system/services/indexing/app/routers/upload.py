"""Upload endpoints for document processing and indexing."""

import os
import shutil
import logging
import requests
from tempfile import TemporaryDirectory
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends

from ..main import get_indexing_service, get_data_loader

logger = logging.getLogger(__name__)
router: APIRouter = APIRouter()


@router.post('/upload')
async def upload_file(
    file: UploadFile = File(...),
    indexing_service=Depends(get_indexing_service),
    data_loader=Depends(get_data_loader)
):
    """Upload and index a file permanently.

    Args:
        file: The file to be uploaded and indexed.

    Returns:
        dict: Confirmation message and indexing stats.
    """
    with TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, file.filename)
        logger.info(f"Processing file: {file.filename}")

        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            logger.info("Starting indexing process...")
            indexing_service.run_indexing(data=temp_path)
            logger.info("Indexing completed successfully!")

            # Notify query service to reload index via internal HTTP call
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
                query_reloaded = False

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
    indexing_service=Depends(get_indexing_service),
):
    """Clear all indexed data.

    Returns:
        dict: Confirmation message.
    """
    from ..main import data_base
    if data_base is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # Clear the FAISS index
        data_base.clear_index()

        # Clear processed data
        indexing_service.clear_data()

        # Clear existing hashes
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
