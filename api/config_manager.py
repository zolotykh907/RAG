import os
import yaml
import logging
from typing import Dict

logger = logging.getLogger(__name__)

ALLOWED_SERVICES = {"indexing", "query"}

def get_config_path(service: str) -> str:
    if service not in ALLOWED_SERVICES:
        raise ValueError(f"Invalid service name: {service}")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, service, 'config.yaml')


def load_config(service: str) -> Dict:
    config_path = get_config_path(service)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file for {service} not found")
    
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        return config_data
    except Exception as e:
        logger.error(f"Failed to read configuration for {service}: {e}")
        raise


def save_config(service: str, config_data: Dict) -> None:
    config_path = get_config_path(service)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file for {service} not found")
    
    try:
        def str_presenter(dumper, data):
            if '\n' in data:
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data)

        yaml.add_representer(str, str_presenter)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                config_data,
                f,
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
