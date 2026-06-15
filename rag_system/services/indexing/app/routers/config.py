"""Configuration management endpoints."""

import logging
import os
from typing import Any, Dict

import requests
from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException

from rag_system.api.config_manager import load_config
from rag_system.api.config_manager import save_config

logger = logging.getLogger(__name__)
router = APIRouter()

_QUERY_SERVICE = "query"


def _query_config_url() -> str:
    """Return the query-service configuration endpoint URL."""
    query_service_url = os.getenv('QUERY_SERVICE_URL', 'http://query:8002')
    return f"{query_service_url}/api/query/config"


def _raise_query_config_error(response: requests.Response) -> None:
    """Raise an HTTPException using query-service response details."""
    try:
        detail: Any = response.json().get("detail")
    except ValueError:
        detail = response.text or "Query service configuration request failed"
    raise HTTPException(status_code=response.status_code, detail=detail)


def _get_query_config() -> Dict[str, Any]:
    """Load query configuration from query-service."""
    try:
        response = requests.get(_query_config_url(), params={"service": _QUERY_SERVICE}, timeout=5)
    except requests.RequestException as e:
        logger.error(f"Failed to contact query service for config read: {e}")
        raise HTTPException(status_code=503, detail="Query service is unavailable")

    if response.status_code >= 400:
        _raise_query_config_error(response)
    return response.json()


def _update_query_config(new_config: Dict[str, Any]) -> Dict[str, Any]:
    """Save query configuration in query-service."""
    try:
        response = requests.post(
            _query_config_url(),
            params={"service": _QUERY_SERVICE},
            json=new_config,
            timeout=5,
        )
    except requests.RequestException as e:
        logger.error(f"Failed to contact query service for config update: {e}")
        raise HTTPException(status_code=503, detail="Query service is unavailable")

    if response.status_code >= 400:
        _raise_query_config_error(response)
    return response.json()


@router.get("/config")
async def get_config(service: str) -> Dict[str, Any]:
    """Get configuration for a specified service.

    Args:
        service: The name of the service (indexing or query).

    Returns:
        Configuration data.

    Raises:
        HTTPException: If the configuration is missing or cannot be read.
    """
    if service == _QUERY_SERVICE:
        return _get_query_config()

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
async def update_config(service: str, new_config: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Update configuration for a specified service.

    Args:
        service: The name of the service.
        new_config: The new configuration data.

    Returns:
        Confirmation message.

    Raises:
        HTTPException: If the configuration is missing or cannot be written.
    """
    if service == _QUERY_SERVICE:
        return _update_query_config(new_config)

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
