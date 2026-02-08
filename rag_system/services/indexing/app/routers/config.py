"""Configuration management endpoints."""

import logging
from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException
from typing import Dict

from rag_system.api.config_manager import load_config
from rag_system.api.config_manager import save_config

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/config")
async def get_config(service: str):
    """Get configuration for a specified service.

    Args:
        service: The name of the service (indexing or query).

    Returns:
        Dict: The configuration data.
    """
    try:
        config_data = load_config(service)
        return config_data
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Configuration file for {service} not found"
        )
    except Exception as e:
        logger.error(f"Failed to get configuration for {service}: {e}")
        raise HTTPException(status_code=500, detail="Error reading configuration")


@router.post("/config")
async def update_config(service: str, new_config: Dict = Body(...)):
    """Update configuration for a specified service.

    Args:
        service: The name of the service.
        new_config: The new configuration data.

    Returns:
        Dict: Confirmation message.
    """
    try:
        save_config(service, new_config)
        return {"message": f"Configuration for {service} updated successfully"}
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Configuration file for {service} not found"
        )
    except Exception as e:
        logger.error(f"Error updating configuration for {service}: {e}")
        raise HTTPException(status_code=500, detail="Error updating configuration")
