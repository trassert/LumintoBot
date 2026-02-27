from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

"Модуль для получения из value телеграма список выпавших предметов"

mapping = {"0": "Бар", "1": "Ягода", "2": "Лимон", "3": "7"}


def get(value: int) -> list[str]:
    return [
        str((value - 1) & 3),
        str(((value - 1) >> 2) & 3),
        str(((value - 1) >> 4) & 3),
    ]
