from random import choice
from os import listdir, path

from . import pathes
from loguru import logger

logger.info(f"Загружен модуль {__name__}!")


def get_random():
    return path.join(pathes.pic, choice(listdir(pathes.pic)))
