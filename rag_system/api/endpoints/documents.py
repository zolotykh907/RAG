import asyncio
import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from fastapi import HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()

# Simple mtime-based cache so processed_data.json is not read on every request
_data_cache: Dict[str, Any] = {"mtime": None, "data": None}


def _load_processed_data(path: str) -> List[Dict[str, Any]]:
    """Load processed_data.json, using a mtime cache to avoid redundant disk reads."""
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return []
    if _data_cache["mtime"] == mtime:
        return _data_cache["data"]
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _data_cache["mtime"] = mtime
    _data_cache["data"] = data
    return data


def _invalidate_cache() -> None:
    _data_cache["mtime"] = None
    _data_cache["data"] = None


def _write_json_atomic(path: str, data: List[Any]) -> None:
    """Write JSON atomically: write to a sibling tmp file then rename."""
    dir_ = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    _invalidate_cache()


@router.get('/documents')
async def get_documents(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """Get list of all indexed documents with metadata (paginated)."""
    import rag_system.api.main as main_module

    if main_module.indexing_service is None:
        raise HTTPException(status_code=503, detail="Indexing service not available.")

    try:
        processed_data_path = main_module.query_config.processed_data_path

        if not os.path.exists(processed_data_path):
            return {"documents": [], "total_chunks": 0}

        data = _load_processed_data(processed_data_path)
        if not data:
            return {"documents": [], "total_chunks": 0}

        documents_map: Dict[str, Any] = {}
        for item in data:
            source = item.get('source')
            if not source or source == 'unknown':
                source = 'Untitled (legacy data)'
            if source not in documents_map:
                documents_map[source] = {
                    'filename': source,
                    'chunks': [],
                    'total_chunks': 0,
                    'total_chars': 0,
                    'first_added': item.get('timestamp', 'N/A')
                }
            documents_map[source]['chunks'].append({
                'text': item.get('text', ''),
                'hash': item.get('hash', ''),
                'index': len(documents_map[source]['chunks'])
            })
            documents_map[source]['total_chunks'] += 1
            documents_map[source]['total_chars'] += len(item.get('text', ''))

        all_documents = list(documents_map.values())
        paginated = all_documents[offset: offset + limit]

        logger.info(f"Found {len(all_documents)} documents with {len(data)} total chunks")
        return {
            "documents": paginated,
            "total_documents": len(all_documents),
            "total_chunks": len(data),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Failed to get documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")


@router.get('/documents/{filename}')
async def get_document_content(filename: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Get content of a specific document (permanent or temporary)."""
    import rag_system.api.main as main_module
    from rag_system.shared.temp_storage import temp_index_manager

    try:
        if session_id:
            temp_data = temp_index_manager.get_temp_file_content(session_id, filename)
            if temp_data and 'chunks' in temp_data:
                chunks = temp_data['chunks']
                return {
                    "filename": filename,
                    "chunks": chunks,
                    "total_chunks": len(chunks),
                    "total_chars": sum(
                        len(chunk.get('text', '')) if isinstance(chunk, dict) else 0
                        for chunk in chunks
                    ),
                    "is_temporary": True
                }

        processed_data_path = main_module.query_config.processed_data_path
        if not os.path.exists(processed_data_path):
            raise HTTPException(status_code=404, detail="No documents found")

        data = _load_processed_data(processed_data_path)
        chunks = [item for item in data if item.get('source') == filename]

        if not chunks:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "filename": filename,
            "chunks": chunks,
            "total_chunks": len(chunks),
            "total_chars": sum(len(chunk.get('text', '')) for chunk in chunks),
            "is_temporary": False
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document content: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document")


@router.get('/search-documents')
async def search_documents(query: str = '') -> Dict[str, Any]:
    """Search documents by content."""
    import rag_system.api.main as main_module

    if not query:
        return {"results": [], "total_results": 0}

    try:
        processed_data_path = main_module.query_config.processed_data_path
        if not os.path.exists(processed_data_path):
            return {"results": [], "total_results": 0}

        data = _load_processed_data(processed_data_path)
        if not data:
            return {"results": [], "total_results": 0}

        query_lower = query.lower()
        matching_chunks = [
            item for item in data
            if query_lower in item.get('text', '').lower()
        ]

        documents_map: Dict[str, Any] = {}
        for item in matching_chunks:
            source = item.get('source', 'unknown')
            if source not in documents_map:
                documents_map[source] = {'filename': source, 'matches': [], 'total_matches': 0}
            text = item.get('text', '')
            documents_map[source]['matches'].append({
                'text': text[:200] + '...' if len(text) > 200 else text,
                'hash': item.get('hash', '')
            })
            documents_map[source]['total_matches'] += 1

        results = list(documents_map.values())
        logger.info(f"Search found {len(results)} documents with {len(matching_chunks)} matches")
        return {"results": results, "total_results": len(matching_chunks)}

    except Exception as e:
        logger.error(f"Failed to search documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.delete('/documents/{filename}')
async def delete_document(filename: str) -> Dict[str, Any]:
    """Delete a specific document and reindex."""
    import rag_system.api.main as main_module

    indexing_svc = main_module.indexing_service
    data_base = main_module.data_base

    if indexing_svc is None:
        raise HTTPException(status_code=503, detail="Indexing service not available.")
    if data_base is None:
        raise HTTPException(status_code=503, detail="Database not available.")

    try:
        processed_data_path = main_module.query_config.processed_data_path
        if not os.path.exists(processed_data_path):
            raise HTTPException(status_code=404, detail="No documents found")

        data = _load_processed_data(processed_data_path)
        filtered_data = [item for item in data if item.get('source') != filename]
        deleted_count = len(data) - len(filtered_data)

        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")

        if filtered_data:
            import faiss
            import numpy as np
            from rag_system.indexing.data_vectorize import save_embeddings
            from rag_system.query.query import Query
            from rag_system.query.pipeline import RAGPipeline

            # Compute embeddings BEFORE writing anything to disk
            embedding_model = indexing_svc.load_local_embedding_model()
            texts = [item['text'] for item in filtered_data]
            loop = asyncio.get_running_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: embedding_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            )
            embeddings = np.array(embeddings, dtype=np.float32)
            faiss.normalize_L2(embeddings)

            # All computation succeeded — now write to disk atomically
            _write_json_atomic(processed_data_path, filtered_data)
            save_embeddings(embeddings, indexing_svc.embeddings_path)
            data_base.create_index(embeddings, replace=True)

            logger.info(f"Deleted '{filename}' ({deleted_count} chunks), reindexed remaining")

            try:
                data_base.load_index()
                query_service = Query(main_module.query_config, data_base)
                pipeline = RAGPipeline(
                    config=main_module.query_config,
                    query=query_service,
                    responder=main_module.responder,
                    redis_client=main_module.redis_client,
                )
                with main_module.services_lock:
                    main_module.query_service = query_service
                    main_module.pipeline = pipeline
                logger.info("Query service reinitialized after document deletion")
            except Exception as e:
                logger.error(f"Failed to reinitialize query service: {e}")
                with main_module.services_lock:
                    main_module.query_service = None
                    main_module.pipeline = None

            # Invalidate Redis cache so stale answers are not served
            if main_module.redis_client is not None:
                main_module.redis_client.flush_cache()

        else:
            data_base.clear_index()
            embeddings_path = indexing_svc.embeddings_path
            if os.path.exists(embeddings_path):
                os.remove(embeddings_path)
            _write_json_atomic(processed_data_path, [])
            logger.info(f"Deleted last document '{filename}', index cleared")

            with main_module.services_lock:
                main_module.query_service = None
                main_module.pipeline = None

            if main_module.redis_client is not None:
                main_module.redis_client.flush_cache()

        return {
            "message": "Document deleted successfully",
            "deleted_chunks": deleted_count,
            "remaining_chunks": len(filtered_data)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete document")
