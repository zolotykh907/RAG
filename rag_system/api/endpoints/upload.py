import asyncio
import os
import shutil
import uuid
import logging
from tempfile import TemporaryDirectory
from typing import Any, Dict, Optional

from fastapi import APIRouter
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import File

from rag_system.api import state
from rag_system.api.services import process_file_temp
from rag_system.api.temp_storage import temp_index_manager
from rag_system.indexing import Indexing
from rag_system.query.query import Query
from rag_system.query.pipeline import RAGPipeline
from rag_system.shared.index_snapshot import IndexSnapshotStore

logger = logging.getLogger(__name__)
router = APIRouter()


def _safe_filename(filename: str) -> str:
    """Return a safe basename for an uploaded file."""
    base = os.path.basename(filename or "").strip().replace("\x00", "")
    if base in ("", ".", ".."):
        base = f"upload-{uuid.uuid4().hex}"
    return base


async def _require_indexing_service() -> Indexing:
    """Return the indexing service, lazily initializing it when needed."""
    indexing_svc = state.indexing_service
    if indexing_svc is not None:
        return indexing_svc

    try:
        return await asyncio.to_thread(state.get_indexing_service)
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        ) from e


@router.post('/upload-temp')
async def upload_temp_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(default=None),
) -> Dict[str, Any]:
    """Upload and temporarily index a file for session use.

    Args:
        file: The file to be uploaded and indexed.
        session_id: Optional existing session identifier.

    Returns:
        Confirmation message with session ID and chunk count.

    Raises:
        HTTPException: If required services are unavailable or temporary indexing fails.
    """
    indexing_svc = await _require_indexing_service()
    data_loader = indexing_svc.data_loader

    try:
        target_session_id = session_id or temp_index_manager.generate_session_id()

        with TemporaryDirectory() as temp_dir:
            safe_name = _safe_filename(file.filename or "upload")
            temp_path = os.path.join(temp_dir, safe_name)
            logger.info(f"Temporary file saved: {temp_path}")

            loop = asyncio.get_running_loop()
            with open(temp_path, "wb") as f:
                await loop.run_in_executor(None, lambda: shutil.copyfileobj(file.file, f))

            temp_data = await loop.run_in_executor(
                None, process_file_temp, temp_path, data_loader, indexing_svc
            )

            temp_index_manager.add_temp_index(target_session_id, temp_data)

            logger.info(f"Temporary file indexed successfully. Session ID: {target_session_id}")
            return {
                "message": "File processed and temporarily indexed successfully.",
                "session_id": target_session_id,
                "chunks_count": len(temp_data['chunks'])
            }

    except ValueError as e:
        logger.warning(f"Temporary indexing rejected: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Temporary indexing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/upload-files')
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload and index a file.

    Args:
        file: The file to be uploaded and indexed.

    Returns:
        Confirmation message indicating successful indexing.

    Raises:
        HTTPException: If required services are unavailable or indexing fails.
    """
    indexing_svc = await _require_indexing_service()
    data_base = indexing_svc.data_base

    with TemporaryDirectory() as temp_dir:
        safe_name = _safe_filename(file.filename or "upload")
        temp_path = os.path.join(temp_dir, safe_name)
        logger.info(f"File saved to temp directory: {temp_path}")
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            logger.info("Start indexing...")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, lambda: indexing_svc.run_indexing(data=temp_path)
            )
            logger.info("End indexing!")

            artifacts = IndexSnapshotStore.from_config(state.query_config).current_artifacts()
            if os.path.exists(artifacts.processed_data_path) and os.path.exists(artifacts.index_path):
                try:
                    data_base.load_index(artifacts.index_path)

                    query_service = Query(state.query_config, data_base)
                    pipeline = RAGPipeline(
                        config=state.query_config,
                        query=query_service,
                        responder=state.responder,
                        redis_client=state.redis_client,
                    )

                    with state.services_lock:
                        state.query_service = query_service
                        state.pipeline = pipeline

                    logger.info('Query service and pipeline reinitialized after indexing.')
                    if state.redis_client is not None:
                        state.redis_client.flush_cache()
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
async def clear_temp_session(session_id: str) -> Dict[str, Any]:
    """Clear temporary session data.

    Args:
        session_id: Temporary session identifier.

    Returns:
        Confirmation message.

    Raises:
        HTTPException: If the session does not exist or clearing fails.
    """
    try:
        if temp_index_manager.remove_temp_index(session_id):
            return {"message": "Session cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/query/sessions/{session_id}')
async def clear_temp_session_alias(session_id: str) -> Dict[str, Any]:
    """Clear temporary session data through the query-compatible route.

    Args:
        session_id: Temporary session identifier.

    Returns:
        Confirmation message from the canonical clear route.
    """
    return await clear_temp_session(session_id)


@router.delete('/clear-index')
async def clear_permanent_index() -> Dict[str, Any]:
    """Clear all permanently indexed data.

    Returns:
        Confirmation message.

    Raises:
        HTTPException: If required services are unavailable or clearing fails.
    """
    indexing_svc = state.indexing_service
    data_base = state.data_base

    if indexing_svc is None:
        raise HTTPException(status_code=503, detail="Indexing service not available.")
    if data_base is None:
        raise HTTPException(status_code=503, detail="Database not available.")

    try:
        data_base.clear_index()
        indexing_svc.clear_data()
        indexing_svc.existing_hashes = []

        with state.services_lock:
            state.query_service = None
            state.pipeline = None

        logger.info("Permanent index cleared successfully")
        return {"message": "All indexed data cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/temp-files/{session_id}')
async def get_temp_files_info(session_id: str) -> Dict[str, Any]:
    """Get metadata for all temporary files in a session.

    Args:
        session_id: Temporary session identifier.

    Returns:
        Temporary file metadata and total count.

    Raises:
        HTTPException: If metadata retrieval fails.
    """
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
            total_chars = sum(len(chunk.get('text', '')) if isinstance(chunk, dict) else 0
                             for chunk in temp_data['chunks'])

            temp_files.append({
                "filename": filename,
                "chunks_count": chunks_count,
                "total_chars": total_chars
            })

        logger.info(f"Found {len(temp_files)} temporary files for session {session_id}")
        return {"temp_files": temp_files, "total_files": len(temp_files)}

    except Exception as e:
        logger.error(f"Failed to get temp files info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/query/sessions/{session_id}/files')
async def get_temp_files_info_alias(session_id: str) -> Dict[str, Any]:
    """Get temporary file metadata through the query-compatible route.

    Args:
        session_id: Temporary session identifier.

    Returns:
        Temporary file metadata from the canonical route.
    """
    return await get_temp_files_info(session_id)


@router.get('/query/sessions/{session_id}/files/{filename}')
async def get_temp_file_content(session_id: str, filename: str) -> Dict[str, Any]:
    """Get temporary file content from the query-compatible route.

    Args:
        session_id: Temporary session identifier.
        filename: Source filename to retrieve.

    Returns:
        Temporary file chunks and aggregate metadata.

    Raises:
        HTTPException: If the file does not exist or retrieval fails.
    """
    try:
        temp_data = temp_index_manager.get_temp_file_content(session_id, filename)
        if not temp_data or 'chunks' not in temp_data:
            raise HTTPException(status_code=404, detail=f"File '{filename}' not found in session {session_id}")

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


@router.delete('/temp-files/{session_id}/{filename}')
async def delete_temp_file(session_id: str, filename: str) -> Dict[str, Any]:
    """Delete a temporary file from a session.

    Args:
        session_id: Temporary session identifier.
        filename: Source filename to delete.

    Returns:
        Confirmation message.

    Raises:
        HTTPException: If the file does not exist or deletion fails.
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


@router.delete('/query/sessions/{session_id}/files/{filename}')
async def delete_temp_file_alias(session_id: str, filename: str) -> Dict[str, Any]:
    """Delete a temporary file through the query-compatible route.

    Args:
        session_id: Temporary session identifier.
        filename: Source filename to delete.

    Returns:
        Confirmation message from the canonical deletion route.
    """
    return await delete_temp_file(session_id, filename)
