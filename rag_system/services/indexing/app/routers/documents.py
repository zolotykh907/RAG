"""Document management endpoints."""

import asyncio
import os
import json
import logging
import requests
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from rag_system.indexing.data_vectorize import create_embeddings
from rag_system.indexing.indexing import Indexing
from rag_system.services.indexing.app import state
from rag_system.shared.index_snapshot import IndexSnapshotStore

logger = logging.getLogger(__name__)
router: APIRouter = APIRouter()


def _get_snapshot_store() -> IndexSnapshotStore:
    """Build a snapshot store from the current indexing config."""
    return IndexSnapshotStore.from_config(state.shared_config)


@router.get('/documents')
async def get_documents():
    """Get list of all indexed documents with metadata.

    Returns:
        List of documents with metadata.

    Raises:
        HTTPException: If document metadata cannot be loaded.
    """
    try:
        processed_data_path = _get_snapshot_store().current_artifacts().processed_data_path

        if not os.path.exists(processed_data_path):
            return {"documents": [], "total_chunks": 0}

        with open(processed_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data:
            return {"documents": [], "total_chunks": 0}

        # Group chunks by source file
        documents_map = {}
        for item in data:
            source = item.get('source', 'unknown')
            if source == 'unknown':
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

        documents = list(documents_map.values())

        logger.info(f"Found {len(documents)} documents with {len(data)} total chunks")
        return {"documents": documents, "total_chunks": len(data)}

    except Exception as e:
        logger.error(f"Failed to get documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/documents/{filename}')
async def get_document_content(filename: str):
    """Get content of a specific document.

    Args:
        filename: Name of the document to retrieve.

    Returns:
        Document content with all chunks.

    Raises:
        HTTPException: If the document is missing or cannot be loaded.
    """
    try:
        processed_data_path = _get_snapshot_store().current_artifacts().processed_data_path

        if not os.path.exists(processed_data_path):
            raise HTTPException(status_code=404, detail="No documents found")

        with open(processed_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Filter chunks for this document
        chunks = [item for item in data if item.get('source') == filename]

        if not chunks:
            raise HTTPException(status_code=404, detail=f"Document '{filename}' not found")

        return {
            "filename": filename,
            "chunks": chunks,
            "total_chunks": len(chunks),
            "total_chars": sum(len(chunk.get('text', '')) for chunk in chunks),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/documents/{filename}')
async def delete_document(
    filename: str,
    indexing_service: Indexing = Depends(state.get_indexing_service)
):
    """Delete a specific document and reindex.

    Args:
        filename: Name of the document to delete.

    Returns:
        Confirmation message with deletion statistics.

    Raises:
        HTTPException: If the database is unavailable, the document is missing, or deletion fails.
    """
    data_base = state.data_base
    if data_base is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        snapshot_store = IndexSnapshotStore.from_config(state.shared_config)
        processed_data_path = snapshot_store.current_artifacts().processed_data_path

        if not os.path.exists(processed_data_path):
            raise HTTPException(status_code=404, detail="No documents found")

        with open(processed_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Filter out chunks from this document
        original_count = len(data)
        filtered_data = [item for item in data if item.get('source') != filename]
        deleted_count = original_count - len(filtered_data)

        if deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"Document '{filename}' not found")

        # Reindex if there's remaining data
        if filtered_data:
            # Use the same helper as the normal indexing path so model-specific
            # preprocessing, such as E5 passage prefixes, stays consistent.
            texts = [item['text'] for item in filtered_data]
            loop = asyncio.get_running_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: create_embeddings(
                    texts,
                    indexing_service.emb_model,
                    batch_size=indexing_service.batch_size,
                    model_name=indexing_service.emb_model_name,
                    is_query=False,
                )
            )

            new_index = data_base.build_index(embeddings)
            snapshot_store.publish(filtered_data, embeddings, new_index)
            data_base.index = new_index

            logger.info(f"Deleted '{filename}' ({deleted_count} chunks), reindexed remaining")

            # Notify query service
            try:
                query_service_url = os.getenv('QUERY_SERVICE_URL', 'http://query:8002')
                requests.post(f"{query_service_url}/api/query/reload", timeout=5)
            except Exception as e:
                logger.warning(f"Failed to notify query service: {str(e)}")
        else:
            # No data left, clear everything
            snapshot_store.clear()
            data_base.index = None

            logger.info(f"Deleted last document '{filename}', index cleared")

            # Notify query service to reset
            try:
                query_service_url = os.getenv('QUERY_SERVICE_URL', 'http://query:8002')
                requests.post(f"{query_service_url}/api/query/reset", timeout=5)
            except Exception as e:
                logger.warning(f"Failed to notify query service: {str(e)}")

        return {
            "message": f"Document '{filename}' deleted successfully",
            "deleted_chunks": deleted_count,
            "remaining_chunks": len(filtered_data)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/search-documents')
async def search_documents(query: str = ''):
    """Search documents by content.

    Args:
        query: Search query string.

    Returns:
        Matching documents grouped by filename.

    Raises:
        HTTPException: If search fails.
    """
    if not query:
        return {"results": [], "total_results": 0}

    try:
        processed_data_path = _get_snapshot_store().current_artifacts().processed_data_path

        if not os.path.exists(processed_data_path):
            return {"results": [], "total_results": 0}

        with open(processed_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data:
            return {"results": [], "total_results": 0}

        # Simple text search
        query_lower = query.lower()
        matching_chunks = []

        for item in data:
            text = item.get('text', '')
            if query_lower in text.lower():
                source = item.get('source', 'unknown')
                matching_chunks.append({
                    'filename': source,
                    'text': text,
                    'hash': item.get('hash', ''),
                    'timestamp': item.get('timestamp', 'N/A')
                })

        # Group by document
        documents_map = {}
        for chunk in matching_chunks:
            filename = chunk['filename']
            if filename not in documents_map:
                documents_map[filename] = {
                    'filename': filename,
                    'matches': [],
                    'total_matches': 0
                }

            documents_map[filename]['matches'].append({
                'text': chunk['text'][:200] + '...' if len(chunk['text']) > 200 else chunk['text'],
                'hash': chunk['hash']
            })
            documents_map[filename]['total_matches'] += 1

        results = list(documents_map.values())

        logger.info(f"Search query '{query}' found {len(results)} documents")
        return {"results": results, "total_results": len(matching_chunks)}

    except Exception as e:
        logger.error(f"Failed to search documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
