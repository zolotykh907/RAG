import yaml


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

        for key, value in cfg_items:
            setattr(self, key, value)


    def reload(self):
        for attr in list(self.__dict__.keys()):
            if attr != "config_file_path":
                delattr(self, attr)
        self.set_items()
