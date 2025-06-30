from loguru import logger
from time import time


class FloodWaitBase:
    def __init__(self, name="FloodWaitSys", timer=5, lasttime=time()):
        logger.info(f"ФлудВайт: {name} инициализирован")
        self.time = lasttime
        self.timer = timer
    def request(self):
        now = time()
        wait = round(now-self.time)
        if wait > self.timer:
            self.time = now
            return True
        return wait