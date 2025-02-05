import logging
from random import choices

logger = logging.getLogger(__name__)


def weighted_choice(strings, weights):
    if not isinstance(strings, list) or \
            not all(isinstance(s, str) for s in strings):
        logger.error("Strings должен быть списком строк.")
        return None

    # Проверка на словарь
    if not isinstance(weights, dict):
        logger.error("Weights должен быть словарем.")
        return None

    # Проверка, что все ключи в weights есть в strings и веса - числа
    valid_weights = {
        k: v for k, v in weights.items()
        if k in strings and isinstance(v, (int, float))
    }
    if not all(v >= 0 for v in valid_weights.values()):
        logger.error("Веса должны быть неотрицательными числами.")
        return None
    if len(valid_weights) == 0:
        logger.error("Нет валидных весов для строк.")
        return None

    # Создаем список весов, соответствующий порядку строк
    probabilities = [valid_weights.get(s, 0) for s in strings]

    # Нормализация веса
    total_weight = sum(probabilities)
    if total_weight > 0:
        normalized_probabilities = [p / total_weight for p in probabilities]
    else:
        normalized_probabilities = probabilities

    try:
        return choices(strings, weights=normalized_probabilities, k=1)[0]
    except IndexError:
        logger.error("Список строк пуст или веса некорректны.")
        return None
