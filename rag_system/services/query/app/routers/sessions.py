"""Session management for temporary uploads and queries."""

import asyncio
import logging
import os
import shutil
import uuid
from tempfile import TemporaryDirectory
from typing import Any, Dict

from fastapi import APIRouter
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile

logger = logging.getLogger(__name__)
router = APIRouter()


def _safe_filename(filename: str) -> str:
    """Return a safe basename for an uploaded file."""
    base = os.path.basename(filename or "").strip().replace("\x00", "")
    if base in ("", ".", ".."):
        base = f"upload-{uuid.uuid4().hex}"
    return base


@router.post('/upload-temp')
async def upload_temp_file(
    file: UploadFile = File(...),
    session_id: str | None = Form(default=None),
) -> Dict[str, Any]:
    """Upload and temporarily index a file for session use.

    Args:
        file: The file to be uploaded and indexed temporarily.
        session_id: Optional existing session identifier.

    Returns:
        Session ID and chunk count.

    Raises:
        HTTPException: If temporary indexing fails.
    """
    import rag_system.services.query.app.main as main_module
    from rag_system.shared.temp_storage import temp_index_manager
    from rag_system.query.combined import process_file_temp

    indexing_service = main_module.temp_indexing_service
    if indexing_service is None:
        raise HTTPException(status_code=503, detail="Indexing service not available")
    data_loader = indexing_service.data_loader

    try:
        target_session_id = session_id or temp_index_manager.generate_session_id()

        with TemporaryDirectory() as temp_dir:
            safe_name = _safe_filename(file.filename or "upload")
            temp_path = os.path.join(temp_dir, safe_name)
            logger.info(f"Processing temporary file: {file.filename}")

            loop = asyncio.get_running_loop()
            with open(temp_path, "wb") as f:
                await loop.run_in_executor(None, lambda: shutil.copyfileobj(file.file, f))

            temp_data = await loop.run_in_executor(
                None, process_file_temp, temp_path, data_loader, indexing_service
            )
            temp_index_manager.add_temp_index(target_session_id, temp_data)

            logger.info(f"Temporary file indexed. Session ID: {target_session_id}")
            return {
                "message": "File processed and temporarily indexed",
                "session_id": target_session_id,
                "chunks_count": len(temp_data['chunks'])
            }

    except ValueError as e:
        logger.warning(f"Temporary indexing rejected: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Temporary indexing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/sessions/{session_id}')
async def clear_session(session_id: str) -> Dict[str, Any]:
    """Clear temporary session data.

    Args:
        session_id: The session ID to clear.

    Returns:
        Confirmation message.

    Raises:
        HTTPException: If the session does not exist or cannot be cleared.
    """
    from rag_system.shared.temp_storage import temp_index_manager

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
async def get_temp_files(session_id: str) -> Dict[str, Any]:
    """Get information about temporary files in a session.

    Args:
        session_id: The session ID.

    Returns:
        List of temporary files.

    Raises:
        HTTPException: If metadata retrieval fails.
    """
    from rag_system.shared.temp_storage import temp_index_manager

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
async def delete_temp_file(session_id: str, filename: str) -> Dict[str, Any]:
    """Delete a specific temporary file from a session.

    Args:
        session_id: The session ID.
        filename: Name of the file to delete.

    Returns:
        Confirmation message.

    Raises:
        HTTPException: If the file does not exist or cannot be deleted.
    """
    from rag_system.shared.temp_storage import temp_index_manager

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


@router.get('/sessions/{session_id}/files/{filename}')
async def get_temp_file_content(session_id: str, filename: str) -> Dict[str, Any]:
    """Get content of a temporary file in a session.

    Args:
        session_id: Temporary session identifier.
        filename: Source filename to retrieve.

    Returns:
        Temporary file chunks and aggregate metadata.

    Raises:
        HTTPException: If the file does not exist or retrieval fails.
    """
    from rag_system.shared.temp_storage import temp_index_manager

    try:
        temp_data = temp_index_manager.get_temp_file_content(session_id, filename)
        if not temp_data or 'chunks' not in temp_data:
            raise HTTPException(
                status_code=404,
                detail=f"File '{filename}' not found in session {session_id}",
            )

        chunks = temp_data['chunks']
        return {
            "filename": filename,
            "chunks": chunks,
            "total_chunks": len(chunks),
            "total_chars": sum(
                len(chunk.get('text', '')) if isinstance(chunk, dict) else 0
                for chunk in chunks
            ),
            "is_temporary": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get temp file content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
