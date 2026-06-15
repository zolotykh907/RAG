"""Configuration management endpoints for query service."""

import logging
from typing import Any, Dict

from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException

from rag_system.api.config_manager import load_config
from rag_system.api.config_manager import save_config

logger = logging.getLogger(__name__)
router = APIRouter()

_SERVICE = "query"


def _validate_service(service: str) -> None:
    """Validate that the request targets query service configuration."""
    if service != _SERVICE:
        raise HTTPException(
            status_code=400,
            detail=f"Query service can only manage '{_SERVICE}' configuration.",
        )


@router.get("/config")
async def get_config(service: str = _SERVICE) -> Dict[str, Any]:
    """Get query service configuration.

    Args:
        service: Service name. Must be ``query``.

    Returns:
        Parsed query service configuration.

    Raises:
        HTTPException: If the service is invalid or configuration cannot be read.
    """
    _validate_service(service)
    try:
        return load_config(service)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Configuration file for {service} not found",
        )
    except Exception as e:
        logger.error(f"Failed to get configuration for {service}: {e}")
        raise HTTPException(status_code=500, detail="Error reading configuration")


@router.post("/config")
async def update_config(
    service: str = _SERVICE,
    new_config: Dict[str, Any] = Body(...),
) -> Dict[str, str]:
    """Update query service configuration.

    Args:
        service: Service name. Must be ``query``.
        new_config: New configuration payload.

    Returns:
        Confirmation message.

    Raises:
        HTTPException: If the service is invalid or configuration cannot be saved.
    """
    _validate_service(service)
    try:
        save_config(service, new_config)
        return {"message": f"Configuration for {service} updated successfully"}
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Configuration file for {service} not found",
        )
    except Exception as e:
        logger.error(f"Error updating configuration for {service}: {e}")
        raise HTTPException(status_code=500, detail="Error updating configuration")
