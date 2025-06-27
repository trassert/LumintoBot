from loguru import logger
from time import time

from . import config

class FloodWaitBase:
    def __init__(self, name="FloodWaitSys", lasttime=time()):
        logger.info(f"ФлудВайт: {name} инициализирован")
        self.time = lasttime
    def request(self):
        now = time()
        wait = round(now-self.time)
        if wait > config.coofs.WaitAI:
            self.time = now
            return True
        return wait