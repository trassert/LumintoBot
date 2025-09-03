from time import time

from . import config
from loguru import logger

logger.info(f"Загружен модуль {__name__}!")


class FloodWaitBase:
    def __init__(self, name="FloodWaitSys", timer=5, lasttime=time()):
        logger.info(f"ФлудВайт: {name} инициализирован")
        self.time = lasttime
        self.timer = timer

    def request(self):
        now = time()
        wait = round(now - self.time)
        if wait > self.timer:
            self.time = now
            return True
        return wait


WaitCasino = FloodWaitBase("WaitCasino", config.flood.casino)
