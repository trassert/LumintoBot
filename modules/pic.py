from os import listdir, path
from random import choice

from loguru import logger

from . import pathes

logger.info(f"Загружен модуль {__name__}!")


def get_random():
    return path.join(pathes.pic, choice(listdir(pathes.pic)))
