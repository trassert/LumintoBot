from random import choice

from loguru import logger

from . import pathes

logger.info(f"Загружен модуль {__name__}!")


def get_random():
    files = [f for f in pathes.pic.iterdir() if f.is_file()]
    return choice(files)
