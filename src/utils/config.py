#config.py
import configparser
from .paths import config_root


class Config:
    def __init__(self):
        path = config_root("config.ini")

        self.config = configparser.ConfigParser()
        self.config.read(path, encoding="utf-8")

    def get(self, section, key, default=None):
        section = section.lower()
        key = key.lower()
        return self.config.get(section, key, fallback=default)


# from utils import config
# cfg = config.Config()
#
# host = cfg.get("database", "host")
# print(host)