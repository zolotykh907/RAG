import os
import json
import logging

from fastapi import APIRouter
from fastapi import HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/documents')
async def get_documents():
    """Get list of all indexed documents with metadata."""
    import rag_system.api.main as main_module

    if main_module.indexing_service is None:
        raise HTTPException(status_code=503, detail="Indexing service not available.")

    try:
        processed_data_path = main_module.query_config.processed_data_path

        if not os.path.exists(processed_data_path):
            return {"documents": []}

        with open(processed_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data:
            return {"documents": []}

        documents_map = {}
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

        documents = list(documents_map.values())

        logger.info(f"Found {len(documents)} documents with {len(data)} total chunks")
        return {"documents": documents, "total_chunks": len(data)}

    except Exception as e:
        logger.error(f"Failed to get documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/documents/{filename}')
async def get_document_content(filename: str, session_id: str | None = None):
    """Get content of a specific document (permanent or temporary)."""
    import rag_system.api.main as main_module
    from rag_system.api.temp_storage import temp_index_manager

    try:
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

        processed_data_path = main_module.query_config.processed_data_path

        if not os.path.exists(processed_data_path):
            raise HTTPException(status_code=404, detail="No documents found")

        with open(processed_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

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
    """Search documents by content."""
    import rag_system.api.main as main_module

    if not query:
        return {"results": [], "total_results": 0}

    try:
        processed_data_path = main_module.query_config.processed_data_path

        if not os.path.exists(processed_data_path):
            return {"results": [], "total_results": 0}

        with open(processed_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data:
            return {"results": [], "total_results": 0}

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
    """Delete a specific document and reindex."""
    import rag_system.api.main as main_module

    if main_module.indexing_service is None:
        raise HTTPException(status_code=503, detail="Indexing service not available.")
    if main_module.data_base is None:
        raise HTTPException(status_code=503, detail="Database not available.")

    try:
        processed_data_path = main_module.query_config.processed_data_path

        if not os.path.exists(processed_data_path):
            raise HTTPException(status_code=404, detail="No documents found")

        with open(processed_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        original_count = len(data)
        filtered_data = [item for item in data if item.get('source') != filename]
        deleted_count = original_count - len(filtered_data)

        if deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"Document '{filename}' not found")

        with open(processed_data_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)

        if filtered_data:
            from rag_system.indexing.data_vectorize import save_embeddings
            from rag_system.query.query import Query
            from rag_system.query.pipeline import RAGPipeline

            embedding_model = main_module.indexing_service.load_local_embedding_model()
            texts = [item['text'] for item in filtered_data]
            embeddings = embedding_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

            save_embeddings(embeddings, main_module.indexing_service.embeddings_path)
            main_module.data_base.create_index(embeddings, replace=True)

            logger.info(f"Deleted document '{filename}' ({deleted_count} chunks) and reindexed remaining documents")

            try:
                main_module.data_base.load_index()
                query_service = Query(main_module.query_config, main_module.data_base)
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
        else:
            main_module.data_base.clear_index()

            embeddings_path = main_module.indexing_service.embeddings_path
            if os.path.exists(embeddings_path):
                os.remove(embeddings_path)

            logger.info(f"Deleted last document '{filename}', index cleared")

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
