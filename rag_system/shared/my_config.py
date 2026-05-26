import logging
from typing import Any, List, Tuple

import yaml

logger = logging.getLogger(__name__)


class Config:
    """Load YAML configuration and expose leaf keys as attributes."""

    def __init__(self, config_file_path: str = 'indexing/config.yaml') -> None:
        self.config_file_path = config_file_path
        self.set_items()

    def get_items(self, elem: Any) -> List[Tuple[str, Any]]:
        """Flatten nested configuration dictionaries into leaf key-value pairs.

        Args:
            elem: Configuration fragment to flatten.

        Returns:
            Leaf key-value pairs discovered in the fragment.
        """
        items: List[Tuple[str, Any]] = []
        if isinstance(elem, dict):
            for key, value in elem.items():
                new_key = str(key)
                if isinstance(value, dict):
                    items.extend(self.get_items(value))
                else:
                    items.append((new_key, value))
        return items

    def set_items(self) -> None:
        """Load the YAML file and set configuration keys as attributes.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            yaml.YAMLError: If the configuration file contains invalid YAML.
        """
        with open(self.config_file_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        cfg_items = self.get_items(cfg)

        seen_keys: dict[str, Any] = {}
        for key, value in cfg_items:
            if key in seen_keys:
                logger.warning(
                    f"Config key collision in {self.config_file_path}: "
                    f"'{key}' appears multiple times. "
                    f"Previous value: {seen_keys[key]!r}, new value: {value!r}. "
                    f"Last value wins."
                )
            seen_keys[key] = value
            setattr(self, key, value)

    def reload(self) -> None:
        """Reload configuration attributes from disk."""
        for attr in list(self.__dict__.keys()):
            if attr != "config_file_path":
                delattr(self, attr)
        self.set_items()
