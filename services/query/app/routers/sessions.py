"""Session management for temporary uploads and queries."""

import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
import os
import shutil
from tempfile import TemporaryDirectory

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post('/upload-temp')
async def upload_temp_file(file: UploadFile = File(...)):
    """Upload and temporarily index a file for session use.

    Args:
        file: The file to be uploaded and indexed temporarily.

    Returns:
        dict: Session ID and chunk count.
    """
    from api.temp_storage import temp_index_manager
    from api.services import process_file_temp
    from shared.data_loader import DataLoader
    from shared.data_base import FaissDB
    from indexing import Indexing
    from my_config import Config as SharedConfig

    try:
        # Initialize minimal indexing service for temp processing
        shared_config = SharedConfig('indexing/config.yaml')
        data_loader = DataLoader(shared_config)
        data_base = FaissDB(shared_config)
        indexing_service = Indexing(shared_config, data_loader, data_base)

        session_id = temp_index_manager.generate_session_id()

        with TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, file.filename)
            logger.info(f"Processing temporary file: {file.filename}")

            with open(temp_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            temp_data = process_file_temp(temp_path, data_loader, indexing_service)
            temp_index_manager.add_temp_index(session_id, temp_data)

            logger.info(f"Temporary file indexed. Session ID: {session_id}")
            return {
                "message": "File processed and temporarily indexed",
                "session_id": session_id,
                "chunks_count": len(temp_data['chunks'])
            }

    except Exception as e:
        logger.error(f"Temporary indexing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/sessions/{session_id}')
async def clear_session(session_id: str):
    """Clear temporary session data.

    Args:
        session_id: The session ID to clear.

    Returns:
        dict: Confirmation message.
    """
    from api.temp_storage import temp_index_manager

    try:
        if temp_index_manager.remove_temp_index(session_id):
            logger.info(f"Session {session_id} cleared")
            return {"message": "Session cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/sessions/{session_id}/files')
async def get_temp_files(session_id: str):
    """Get information about temporary files in a session.

    Args:
        session_id: The session ID.

    Returns:
        dict: List of temporary files.
    """
    from api.temp_storage import temp_index_manager

    try:
        temp_data_list = temp_index_manager.get_temp_index(session_id)

        if not temp_data_list:
            return {"temp_files": [], "total_files": 0}

        temp_files = []
        for temp_data in temp_data_list:
            if 'chunks' not in temp_data or not temp_data['chunks']:
                continue

            filename = "Unknown"
            if temp_data['chunks'] and len(temp_data['chunks']) > 0:
                first_chunk = temp_data['chunks'][0]
                if isinstance(first_chunk, dict) and 'source' in first_chunk:
                    filename = first_chunk['source']

            chunks_count = len(temp_data['chunks'])
            total_chars = sum(
                len(chunk.get('text', '')) if isinstance(chunk, dict) else 0
                for chunk in temp_data['chunks']
            )

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
        logger.error(f"Failed to get temp files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/sessions/{session_id}/files/{filename}')
async def delete_temp_file(session_id: str, filename: str):
    """Delete a specific temporary file from a session.

    Args:
        session_id: The session ID.
        filename: Name of the file to delete.

    Returns:
        dict: Confirmation message.
    """
    from api.temp_storage import temp_index_manager

    try:
        removed = temp_index_manager.remove_temp_file(session_id, filename)

        if not removed:
            raise HTTPException(
                status_code=404,
                detail=f"File '{filename}' not found in session {session_id}"
            )

        logger.info(f"Deleted temp file '{filename}' from session {session_id}")
        return {"message": f"File '{filename}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete temp file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
