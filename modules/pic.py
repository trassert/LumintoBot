from random import choice
from os import listdir, path

from . import pathes


def get_random():
    return path.join(pathes.pic_path, choice(listdir(pathes.pic_path)))
