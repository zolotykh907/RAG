import os
import shutil
from tempfile import TemporaryDirectory
from fastapi import APIRouter, HTTPException, UploadFile, File
import logging

from ..services import process_file_temp
from ..temp_storage import temp_index_manager
from query.query import Query
from query.pipeline import RAGPipeline

logger = logging.getLogger(__name__)
router = APIRouter()


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
            temp_path = os.path.join(temp_dir, file.filename)
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
    from ..main import indexing_service, query_config, data_base, responder
    
    if indexing_service is None:
        raise HTTPException(
            status_code=503, 
            detail="Indexing service not available. Please check configuration and try again."
        )
   
    with TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, file.filename)
        logger.info(f"File saved to temp directory: {temp_path}")
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            logger.info("Start indexing...")
            indexing_service.run_indexing(data=temp_path)
            logger.info("End indexing!")
           
            try:
                query_service = Query(query_config, data_base)
                pipeline = RAGPipeline(config=query_config, query=query_service, responder=responder)
                logger.info('Query service and pipeline reinitialized after indexing.')
                return {"message": "File processed and indexed successfully.", "query_service_restarted": True}
            except Exception as e:
                logger.warning(f'Failed to reinitialize query service after indexing: {str(e)}')
                return {"message": "File processed and indexed successfully.", "query_service_restarted": False}
           
        except Exception as e:
            logger.error(f"Indexing failed: {str(e)}")
            return {"error": str(e)}


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