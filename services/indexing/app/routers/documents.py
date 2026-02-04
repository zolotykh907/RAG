"""Document management endpoints."""

import os
import json
import logging
import requests
from fastapi import APIRouter, HTTPException, Depends

from ..main import get_indexing_service, shared_config

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/documents')
async def get_documents():
    """Get list of all indexed documents with metadata.

    Returns:
        dict: List of documents with metadata.
    """
    try:
        processed_data_path = shared_config.processed_data_path

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
                source = 'Без названия (старые данные)'

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
        dict: Document content with all chunks.
    """
    try:
        processed_data_path = shared_config.processed_data_path

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
    indexing_service=Depends(get_indexing_service)
):
    """Delete a specific document and reindex.

    Args:
        filename: Name of the document to delete.

    Returns:
        dict: Confirmation message.
    """
    from ..main import data_base
    if data_base is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        processed_data_path = shared_config.processed_data_path

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

        # Save filtered data
        with open(processed_data_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)

        # Reindex if there's remaining data
        if filtered_data:
            # Re-create embeddings and index
            from indexing.data_vectorize import save_embeddings

            embedding_model = indexing_service.load_local_embedding_model()
            texts = [item['text'] for item in filtered_data]
            embeddings = embedding_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

            # Save embeddings
            save_embeddings(embeddings, indexing_service.embeddings_path)

            # Recreate index
            data_base.create_index(embeddings, replace=True)

            logger.info(f"Deleted '{filename}' ({deleted_count} chunks), reindexed remaining")

            # Notify query service
            try:
                query_service_url = os.getenv('QUERY_SERVICE_URL', 'http://query:8002')
                requests.post(f"{query_service_url}/api/query/reload", timeout=5)
            except Exception as e:
                logger.warning(f"Failed to notify query service: {str(e)}")
        else:
            # No data left, clear everything
            data_base.clear_index()

            if os.path.exists(indexing_service.embeddings_path):
                os.remove(indexing_service.embeddings_path)

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
        dict: List of matching documents.
    """
    if not query:
        return {"results": [], "total_results": 0}

    try:
        processed_data_path = shared_config.processed_data_path

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
