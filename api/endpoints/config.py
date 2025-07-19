from fastapi import APIRouter, HTTPException, Body
import logging
from typing import Dict

from ..config_manager import load_config, save_config

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/config")
async def get_config(service: str):
    """Получить текущую конфигурацию для указанного сервиса."""
    try:
        config_data = load_config(service)
        return config_data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Конфигурационный файл для {service} не найден")
    except Exception as e:
        logger.error(f"Не удалось прочитать конфигурацию для {service}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при чтении конфигурации")


@router.post("/config")
async def update_config(service: str, new_config: Dict = Body(...)):
    """Обновить конфигурацию для указанного сервиса."""
    try:
        save_config(service, new_config)
        return {"message": f"Конфигурация для {service} обновлена успешно"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Конфигурационный файл для {service} не найден")
    except Exception as e:
        logger.error(f"Ошибка при обновлении конфигурации для {service}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении конфигурации") 