import os
import shutil
import uuid
from tempfile import TemporaryDirectory
from fastapi import APIRouter, HTTPException, UploadFile, File
import logging

from ..services import process_file_temp
from ..temp_storage import temp_index_manager
from query.query import Query
from query.pipeline import RAGPipeline

logger = logging.getLogger(__name__)
router = APIRouter()

def _safe_filename(filename: str) -> str:
    base = os.path.basename(filename or "").strip().replace("\x00", "")
    if base in ("", ".", ".."):
        base = f"upload-{uuid.uuid4().hex}"
    return base


@router.post('/upload-temp')
async def upload_temp_file(file: UploadFile = File(...)):
    """Upload and temporarily index a file for session use.

    Args:
        file (UploadFile): The file to be uploaded and indexed.

    Returns:
        dict: Confirmation message with session ID and chunk count."""
    from ..main import indexing_service, data_loader

    if indexing_service is None:
        raise HTTPException(
            status_code=503,
            detail="Indexing service not available. Please check configuration and try again."
        )

    try:
        session_id = temp_index_manager.generate_session_id()

        with TemporaryDirectory() as temp_dir:
            safe_name = _safe_filename(file.filename)
            temp_path = os.path.join(temp_dir, safe_name)
            logger.info(f"Temporary file saved: {temp_path}")

            with open(temp_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            temp_data = process_file_temp(temp_path, data_loader, indexing_service)

            temp_index_manager.add_temp_index(session_id, temp_data)

            logger.info(f"Temporary file indexed successfully. Session ID: {session_id}")
            return {
                "message": "File processed and temporarily indexed successfully.",
                "session_id": session_id,
                "chunks_count": len(temp_data['chunks'])
            }

    except Exception as e:
        logger.error(f"Temporary indexing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/upload-files')
async def upload_file(file: UploadFile = File(...)):
    """Upload and index a file.

    Args:
        file (UploadFile): The file to be uploaded and indexed.

    Returns:
        dict: Confirmation message indicating successful indexing.
    """
    from ..main import indexing_service, query_config, data_base, responder, redis_client

    if indexing_service is None:
        raise HTTPException(
            status_code=503,
            detail="Indexing service not available. Please check configuration and try again."
        )
    if data_base is None:
        raise HTTPException(status_code=503, detail="Database not available.")

    with TemporaryDirectory() as temp_dir:
        safe_name = _safe_filename(file.filename)
        temp_path = os.path.join(temp_dir, safe_name)
        logger.info(f"File saved to temp directory: {temp_path}")
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            logger.info("Start indexing...")
            indexing_service.run_indexing(data=temp_path)
            logger.info("End indexing!")

            # Check if data file exists before reinitializing
            if os.path.exists(query_config.processed_data_path) and os.path.exists(query_config.index_path):
                try:
                    import api.main as main_module

                    # Reload the database index
                    data_base.load_index(query_config.index_path)

                    query_service = Query(query_config, data_base)
                    pipeline = RAGPipeline(config=query_config, query=query_service, responder=responder, redis_client=redis_client)

                    # Update global variables under lock
                    with main_module.services_lock:
                        main_module.query_service = query_service
                        main_module.pipeline = pipeline

                    logger.info('Query service and pipeline reinitialized after indexing.')
                    return {"message": "File processed and indexed successfully.", "query_service_restarted": True}
                except Exception as e:
                    logger.warning(f'Failed to reinitialize query service after indexing: {str(e)}')
                    return {"message": "File processed and indexed successfully.", "query_service_restarted": False}
            else:
                logger.warning('Data files not found after indexing, skipping query service reinitialization.')
                return {"message": "File processed and indexed successfully.", "query_service_restarted": False}

        except Exception as e:
            logger.error(f"Indexing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


@router.delete('/clear-temp/{session_id}')
async def clear_temp_session(session_id: str):
    """Clear temporary session data.

    Args:
        session_id (str): The ID of the session to clear.

    Returns:
        dict: Confirmation message indicating successful session clearance.
    """
    try:
        if temp_index_manager.remove_temp_index(session_id):
            return {"message": "Session cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        logger.error(f"Failed to clear session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/clear-index')
async def clear_permanent_index():
    """Clear all permanently indexed data.

    Returns:
        dict: Confirmation message indicating successful index clearance.
    """
    from ..main import indexing_service, data_base
    import api.main as main_module

    if indexing_service is None:
        raise HTTPException(
            status_code=503,
            detail="Indexing service not available."
        )
    if data_base is None:
        raise HTTPException(status_code=503, detail="Database not available.")

    try:
        # Clear the index
        data_base.clear_index()

        # Clear processed data
        indexing_service.clear_data()

        # Clear existing hashes in memory
        indexing_service.existing_hashes = []

        # Reset query service and pipeline
        with main_module.services_lock:
            main_module.query_service = None
            main_module.pipeline = None

        logger.info("Permanent index cleared successfully")
        return {"message": "All indexed data cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/temp-files/{session_id}')
async def get_temp_files_info(session_id: str):
    """Get information about all temporary files for a specific session.

    Args:
        session_id (str): The session ID to get temp files info for.

    Returns:
        dict: List of temporary files info including filename, chunks count, etc.
    """
    try:
        temp_data_list = temp_index_manager.get_temp_index(session_id)

        if not temp_data_list:
            return {"temp_files": [], "total_files": 0}

        temp_files = []

        for temp_data in temp_data_list:
            if 'chunks' not in temp_data or not temp_data['chunks']:
                continue

            # Extract filename from first chunk if available
            filename = "Unknown"
            if temp_data['chunks'] and len(temp_data['chunks']) > 0:
                first_chunk = temp_data['chunks'][0]
                if isinstance(first_chunk, dict) and 'source' in first_chunk:
                    filename = first_chunk['source']

            chunks_count = len(temp_data['chunks'])
            total_chars = sum(len(chunk.get('text', '')) if isinstance(chunk, dict) else 0
                             for chunk in temp_data['chunks'])

            temp_files.append({
                "filename": filename,
                "chunks_count": chunks_count,
                "total_chars": total_chars
            })

        logger.info(f"Found {len(temp_files)} temporary files for session {session_id}")
        return {
            "temp_files": temp_files,
            "total_files": len(temp_files)
        }

    except Exception as e:
        logger.error(f"Failed to get temp files info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/temp-files/{session_id}/{filename}')
async def delete_temp_file(session_id: str, filename: str):
    """Delete a specific temporary file from a session.

    Args:
        session_id (str): The session ID.
        filename (str): Name of the file to delete.

    Returns:
        dict: Confirmation message.
    """
    try:
        removed = temp_index_manager.remove_temp_file(session_id, filename)

        if not removed:
            raise HTTPException(status_code=404, detail=f"File '{filename}' not found in session {session_id}")

        logger.info(f"Deleted temporary file '{filename}' from session {session_id}")
        return {"message": f"File '{filename}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete temp file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
