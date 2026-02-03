from bestconfig import Config
from loguru import logger

from . import pathes

logger.info(f"Загружен модуль {__name__}!")

cfg = Config(pathes.config / "config.yml")
tokens = Config(pathes.config / "tokens.yml")
chats = Config(pathes.config / "chats.yml")
