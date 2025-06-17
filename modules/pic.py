from random import choice
from os import listdir, path

from . import patches

def get_random():
    return path.join(
        patches.pic_path,
        choice(listdir(patches.pic_path))
    )