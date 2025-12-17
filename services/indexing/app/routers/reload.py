"""Service reload endpoints."""

import logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/reload")
async def reload_service(service: str):
    """Reload a service with new configuration.

    Args:
        service: The name of the service to reload.

    Returns:
        Dict: Status message.
    """
    try:
        if service == "indexing":
            # Reload indexing service
            from ..main import initialize_services
            initialize_services()
            logger.info("Indexing service reloaded successfully")
            return {"message": "Indexing service reloaded successfully"}

        elif service == "query":
            # Notify query service to reload via HTTP
            import requests
            import os
            query_service_url = os.getenv('QUERY_SERVICE_URL', 'http://query:8002')
            response = requests.post(f"{query_service_url}/api/query/reload", timeout=5)

            if response.status_code == 200:
                logger.info("Query service reloaded successfully")
                return {"message": "Query service reloaded successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to reload query service")

        else:
            raise HTTPException(status_code=400, detail=f"Unknown service: {service}")

    except Exception as e:
        logger.error(f"Failed to reload {service}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
