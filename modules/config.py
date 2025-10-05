from bestconfig import Config

from os import path
from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

tokens = Config(path.join("configs", "tokens.yml"))
coofs = Config(path.join("configs", "coofs.yml"))
chats = Config(path.join("configs", "chats.yml"))
flood = Config(path.join("configs", "flood.yml"))
vars = Config(path.join("configs", "vars.yml"))