import os
import yaml
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def get_config_path(service: str) -> str:
    """Возвращает путь к конфигурационному файлу в зависимости от сервиса."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, service, 'config.yaml')


def load_config(service: str) -> Dict:
    """Загрузить конфигурацию для указанного сервиса."""
    config_path = get_config_path(service)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Конфигурационный файл для {service} не найден")
    
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        return config_data
    except Exception as e:
        logger.error(f"Не удалось прочитать конфигурацию для {service}: {e}")
        raise


def save_config(service: str, config_data: Dict) -> None:
    """Сохранить конфигурацию для указанного сервиса."""
    config_path = get_config_path(service)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Конфигурационный файл для {service} не найден")
    
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
        
        logger.info(f"Конфигурация для {service} успешно сохранена.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении конфигурации для {service}: {e}")
        raise 