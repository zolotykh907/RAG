import yaml


class Config:
    def __init__(self, config_file_path='indexing/config.yaml'):
        with open(config_file_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        cfg_items = self.get_items(cfg)

        for key, value in cfg_items:
            setattr(self, key, value)


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