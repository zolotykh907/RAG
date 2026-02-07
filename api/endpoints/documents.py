import os
import json
import logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/documents')
async def get_documents():
    """Get list of all indexed documents with metadata.

    Returns:
        dict: List of documents with metadata (filename, chunks count, date added, size)
    """
    from ..main import indexing_service, query_config

    if indexing_service is None:
        raise HTTPException(
            status_code=503,
            detail="Indexing service not available."
        )

    try:
        processed_data_path = query_config.processed_data_path

        if not os.path.exists(processed_data_path):
            return {"documents": []}

        with open(processed_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data:
            return {"documents": []}

        # Group chunks by source file
        documents_map = {}
        for item in data:
            # Handle old data without source field
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

        # Convert to list
        documents = list(documents_map.values())

        logger.info(f"Found {len(documents)} documents with {len(data)} total chunks")
        return {"documents": documents, "total_chunks": len(data)}

    except Exception as e:
        logger.error(f"Failed to get documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/documents/{filename}')
async def get_document_content(filename: str, session_id: str | None = None):
    """Get content of a specific document (permanent or temporary).

    Args:
        filename (str): Name of the document to retrieve
        session_id (str, optional): Session ID for temporary files

    Returns:
        dict: Document content with all chunks
    """
    from ..main import query_config
    from ..temp_storage import temp_index_manager

    try:
        # If session_id is provided, try to get temp file first
        if session_id:
            temp_data = temp_index_manager.get_temp_file_content(session_id, filename)
            if temp_data and 'chunks' in temp_data:
                chunks = temp_data['chunks']
                return {
                    "filename": filename,
                    "chunks": chunks,
                    "total_chunks": len(chunks),
                    "total_chars": sum(len(chunk.get('text', '')) if isinstance(chunk, dict) else 0
                                      for chunk in chunks),
                    "is_temporary": True
                }

        # Otherwise, get from permanent storage
        processed_data_path = query_config.processed_data_path

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
            "is_temporary": False
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/search-documents')
async def search_documents(query: str = ''):
    """Search documents by content.

    Args:
        query (str): Search query to match against document content

    Returns:
        dict: List of documents with matching content and their relevance
    """
    from ..main import query_config

    if not query:
        return {"results": [], "total_results": 0}

    try:
        processed_data_path = query_config.processed_data_path

        if not os.path.exists(processed_data_path):
            return {"results": [], "total_results": 0}

        with open(processed_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data:
            return {"results": [], "total_results": 0}

        # Search in chunks
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

        logger.info(f"Search query '{query}' found {len(results)} documents with {len(matching_chunks)} total matches")
        return {"results": results, "total_results": len(matching_chunks)}

    except Exception as e:
        logger.error(f"Failed to search documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/documents/{filename}')
async def delete_document(filename: str):
    """Delete a specific document and reindex.

    Args:
        filename (str): Name of the document to delete

    Returns:
        dict: Confirmation message
    """
    from ..main import indexing_service, query_config, data_base
    import api.main as main_module

    if indexing_service is None:
        raise HTTPException(
            status_code=503,
            detail="Indexing service not available."
        )
    if data_base is None:
        raise HTTPException(status_code=503, detail="Database not available.")

    try:
        processed_data_path = query_config.processed_data_path

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
            # Re-create embeddings and index for remaining data
            from indexing.data_vectorize import save_embeddings

            # Load embedding model
            embedding_model = indexing_service.load_local_embedding_model()

            # Generate embeddings for remaining texts
            texts = [item['text'] for item in filtered_data]
            embeddings = embedding_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

            # Save embeddings
            embeddings_path = indexing_service.embeddings_path
            save_embeddings(embeddings, embeddings_path)

            # Recreate index
            data_base.create_index(embeddings, replace=True)

            logger.info(f"Deleted document '{filename}' ({deleted_count} chunks) and reindexed remaining documents")

            # Reinitialize query service with new data
            try:
                from query.query import Query
                from query.pipeline import RAGPipeline
                from ..main import redis_client, responder

                data_base.load_index()
                query_service = Query(query_config, data_base)
                pipeline = RAGPipeline(config=query_config, query=query_service, responder=responder, redis_client=redis_client)

                with main_module.services_lock:
                    main_module.query_service = query_service
                    main_module.pipeline = pipeline
                logger.info("Query service reinitialized after document deletion")
            except Exception as e:
                logger.error(f"Failed to reinitialize query service: {e}")
                with main_module.services_lock:
                    main_module.query_service = None
                    main_module.pipeline = None
        else:
            # No data left, clear everything
            data_base.clear_index()

            # Remove embeddings file
            embeddings_path = indexing_service.embeddings_path
            if os.path.exists(embeddings_path):
                os.remove(embeddings_path)

            logger.info(f"Deleted last document '{filename}', index cleared")

            # Reset query service
            with main_module.services_lock:
                main_module.query_service = None
                main_module.pipeline = None

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
