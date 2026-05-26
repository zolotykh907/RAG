import os
import logging
from typing import Any, Dict, Set, Tuple

import yaml

logger = logging.getLogger(__name__)

ALLOWED_SERVICES: Set[str] = {"indexing", "query"}

# Keys that must not be changed via the API: filesystem paths and external URLs.
# Changing these could allow SSRF (data_url), path traversal, or data redirection.
_BLOCKED_KEY_PATHS: Dict[str, Set[Tuple[str, str]]] = {
    "indexing": {
        ("data", "data_url"),
        ("data", "data_dir"),
        ("data", "data_path"),
        ("data", "index_path"),
        ("data", "hashes_path"),
        ("data", "processed_data_path"),
        ("data", "quality_log_path"),
        ("data", "logs_dir"),
    },
    "query": {
        ("data", "index_path"),
        ("data", "processed_data_path"),
        ("data", "logs_dir"),
        ("api", "lm_studio_host"),
    },
}


def get_config_path(service: str) -> str:
    """Resolve the configuration file path for a supported service.

    Args:
        service: Service name to resolve.

    Returns:
        Absolute path to the service configuration file.

    Raises:
        ValueError: If the service name is not supported.
    """
    if service not in ALLOWED_SERVICES:
        raise ValueError(f"Invalid service name: {service}")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, service, 'config.yaml')


def load_config(service: str) -> Dict[str, Any]:
    """Load a service configuration from YAML.

    Args:
        service: Service name to load.

    Returns:
        Parsed configuration data.

    Raises:
        ValueError: If the service name is not supported.
        FileNotFoundError: If the configuration file does not exist.
        Exception: If the YAML file cannot be read or parsed.
    """
    config_path = get_config_path(service)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file for {service} not found")

    try:
        with open(config_path, 'r') as f:
            config_data: Dict[str, Any] = yaml.safe_load(f)
        return config_data
    except Exception as e:
        logger.error(f"Failed to read configuration for {service}: {e}")
        raise


def _validate_config(service: str, new_config: Dict[str, Any], current_config: Dict[str, Any]) -> None:
    """Raise when an incoming config changes protected keys."""
    blocked = _BLOCKED_KEY_PATHS.get(service, set())
    for section, key in blocked:
        new_val = (new_config.get(section) or {}).get(key)
        cur_val = (current_config.get(section) or {}).get(key)
        if new_val is not None and new_val != cur_val:
            raise ValueError(
                f"Changing '{section}.{key}' via the API is not allowed "
                f"(filesystem paths and external URLs are read-only)."
            )


def save_config(service: str, config_data: Dict[str, Any]) -> None:
    """Validate and save a service configuration to YAML.

    Args:
        service: Service name to update.
        config_data: Configuration data to persist.

    Raises:
        ValueError: If the service is invalid or protected keys are changed.
        FileNotFoundError: If the configuration file does not exist.
        Exception: If the YAML file cannot be written.
    """
    config_path = get_config_path(service)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file for {service} not found")

    # Load current config and validate the diff
    with open(config_path, 'r') as f:
        current: Dict[str, Any] = yaml.safe_load(f) or {}
    _validate_config(service, config_data, current)

    try:
        class _CustomDumper(yaml.Dumper):
            """YAML dumper that preserves multiline strings."""

            pass

        def _str_presenter(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
            """Represent multiline strings as block scalars."""
            if '\n' in data:
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data)

        _CustomDumper.add_representer(str, _str_presenter)

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                config_data,
                f,
                Dumper=_CustomDumper,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
                width=float("inf"),
                indent=2
            )

        logger.info(f"Configuration for {service} saved successfully.")
    except Exception as e:
        logger.error(f"Error saving configuration for {service}: {e}")
        raise
