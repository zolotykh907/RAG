import logging
import yaml

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, config_file_path='indexing/config.yaml'):
        self.config_file_path = config_file_path
        self.set_items()

    def get_items(self, elem):
        items = []
        if isinstance(elem, dict):
            for key, value in elem.items():
                new_key = str(key)
                if isinstance(value, dict):
                    items.extend(self.get_items(value))
                else:
                    items.append((new_key, value))
        return items

    def set_items(self):
        with open(self.config_file_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        cfg_items = self.get_items(cfg)

        seen_keys = {}
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

    def reload(self):
        for attr in list(self.__dict__.keys()):
            if attr != "config_file_path":
                delattr(self, attr)
        self.set_items()
