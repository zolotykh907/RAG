from fastapi import APIRouter, HTTPException, Body
import logging
from typing import Dict

from ..config_manager import load_config, save_config

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/config")
async def get_config(service: str):
    """Get configuration for a specified service.

    Args:
        service (str): The name of the service to get configuration for service.

    Returns:
        Dict: The configuration data for the specified service."""
    try:
        config_data = load_config(service)
        return config_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Configuration file for {service} not found")
    except Exception as e:
        logger.error(f"Failed get configuration file for {service}: {e}")
        raise HTTPException(status_code=500, detail="Error reading configuration")


@router.post("/config")
async def update_config(service: str, new_config: Dict = Body(...)):
    """Update configuration for a specified service.
    Args:
        service (str): The name of the service to update configuration for.
        new_config (Dict): The new configuration data to save.

    Returns:
        Dict: Confirmation message indicating successful update."""
    try:
        save_config(service, new_config)
        return {"message": f"Configuration for {service} updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Configuration file for {service} not found")
    except Exception as e:
        logger.error(f"Error updating configuration for {service}: {e}")
        raise HTTPException(status_code=500, detail="Error updating configuration")
