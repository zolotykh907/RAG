"""Configuration management endpoints."""

import os
import sys
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Body
from typing import Dict

# Add api to path for config_manager
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root / 'api'))

from config_manager import load_config, save_config

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
        return {"message": f"Конфигурация для {service} обновлена успешно"}
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Конфигурационный файл для {service} не найден"
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении конфигурации для {service}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении конфигурации")
