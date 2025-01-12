import json
import logging

from os import path, listdir
from datetime import datetime, timedelta
from random import choice
from time import time

logger = logging.getLogger(__name__)


def settings(key, value=None, delete=None, log=True):
    "Изменить/получить ключ из настроек"
    if value is not None:
        if log:
            logger.info(f"Значение {key} теперь {value}")
        try:
            with open(
                path.join('db', 'data.json'), "r", encoding="utf-8"
            ) as f:
                data = json.load(f)
            with open(
                path.join('db', 'data.json'), "w", encoding="utf-8"
            ) as f:
                data[key] = value
                data = dict(sorted(data.items()))
                return json.dump(
                    data, f, indent=4, ensure_ascii=False, sort_keys=True
                    )
        except FileNotFoundError:
            logger.error("Файл не найден")
            with open(
                path.join('db', 'data.json'), "w", encoding="utf-8"
            ) as f:
                data = {}
                data[key] = value
                return json.dump(data, f, indent=4, sort_keys=True)
        except json.decoder.JSONDecodeError:
            logger.error("Ошибка при чтении файла")
            with open(
                path.join('db', 'data.json'), "w", encoding="utf-8"
            ) as f:
                json.dump({}, f, indent=4)
            return None
    elif delete is not None:
        if log:
            logger.info(f"Удаляю ключ: {key}")
        with open(
            path.join('db', 'data.json'), "r", encoding="utf-8"
        ) as f:
            data = json.load(f)
        with open(
            path.join('db', 'data.json'), "w", encoding="utf-8"
        ) as f:
            if key in data:
                del data[key]
            return json.dump(
                data, f, indent=4, ensure_ascii=False, sort_keys=True
                )
    else:
        if log:
            logger.info(f"Получаю ключ: {key}")
        try:
            with open(
                path.join('db', 'data.json'), "r", encoding="utf-8"
            ) as f:
                data = json.load(f)
                return data.get(key)
        except json.decoder.JSONDecodeError:
            logger.error("Ошибка при чтении файла")
            with open(
                path.join('db', 'data.json'), "w", encoding="utf-8"
            ) as f:
                json.dump({}, f, indent=4)
            return None
        except FileNotFoundError:
            logger.error("Файл не найден")
            with open(
                path.join('db', 'data.json'), "w", encoding="utf-8"
            ) as f:
                json.dump({}, f, indent=4)
            return None


def add_stat(id):
    'Добавляет статистику'

    now = datetime.now().strftime("%Y.%m.%d")
    'Если для пользователя нет файла'
    if not path.exists(path.join('db', 'user_stats', f'{id}.json')):
        with open(
            path.join('db', 'user_stats', f'{id}.json'),
            'w',
            encoding='utf8'
        ) as f:
            stats = {}
            stats[now] = 1
            return json.dump(
                stats, f, indent=4, ensure_ascii=False, sort_keys=True
            )

    'Если для пользователя есть файл'
    with open(
        path.join('db', 'user_stats', f'{id}.json'), 'r', encoding='utf8'
    ) as f:
        stats = json.load(f)
        if now in stats:
            stats[now] += 1
        else:
            stats[now] = 1
    with open(
        path.join('db', 'user_stats', f'{id}.json'), 'w', encoding='utf8'
    ) as f:
        return json.dump(
            stats, f, indent=4, ensure_ascii=False, sort_keys=True
        )


def give_stat(id, days=1):
    now = datetime.now().strftime("%Y.%m.%d")

    'Если нет файла'
    if not path.exists(path.join('db', 'user_stats', f'{id}.json')):
        with open(
            path.join('db', 'user_stats', f'{id}.json'),
            'w',
            encoding='utf8'
        ) as f:
            stats = {}
            stats[now] = 1
            json.dump(
                stats, f, indent=4, ensure_ascii=False, sort_keys=True
            )
            return 1

    'Если есть файл'
    with open(
        path.join('db', 'user_stats', f'{id}.json'), 'r', encoding='utf8'
    ) as f:
        now = datetime.now()
        stats = json.load(f)
        dates = list(stats.keys())
        dates.sort(reverse=True)
        start_date = now - timedelta(days=days)
        filtered_data = {
            date: value for date, value in stats.items() if datetime.strptime(
                date, '%Y.%m.%d') >= start_date
        }
        return sum(filtered_data.values()) or 1


def get_active(days=1, reverse=True):
    'Получить актив пользователей'

    data = {}
    for file in listdir(path.join('db', 'user_stats')):
        id = file.replace('.json', '')
        data[id] = give_stat(id, days)
    return sorted(data.items(), key=lambda item: item[1], reverse=reverse)


def get_money(id):
    id = str(id)
    with open(
        path.join('db', 'money.json'), 'r', encoding='utf8'
    ) as f:
        data = json.load(f)
        if id in data:
            return data[id]

    with open(
        path.join('db', 'money.json'), 'w', encoding='utf8'
    ) as f:
        data[id] = 0
        json.dump(
            data, f, indent=4, ensure_ascii=False, sort_keys=True
        )
        return 0


def add_money(id, count):
    id = str(id)
    with open(
        path.join('db', 'money.json'), 'r', encoding='utf8'
    ) as f:
        data = json.load(f)
        if id in data:
            data[id] = data[id] + count
        else:
            data[id] = count

    if data[id] < 0:
        data[id] = 0
    with open(
        path.join('db', 'money.json'), 'w', encoding='utf8'
    ) as f:
        json.dump(
            data, f, indent=4, ensure_ascii=False, sort_keys=True
        )
        return data[id]


def give_id_by_nick_minecraft(nick):
    'Получить ид игрока по нику'
    with open(
        path.join('db', 'minecraft.json'), 'r', encoding='utf8'
    ) as f:
        data = json.load(f)
        if nick in data:
            return data[nick]
        return None


def give_nick_by_id_minecraft(id):
    'Получить никнейм игрока по ид'
    with open(
        path.join('db', 'minecraft.json'), 'r', encoding='utf8'
    ) as f:
        data = json.load(f)
        for key, value in data.items():
            if value == id:
                return key
        return None


def add_nick_minecraft(nick, id):
    'Связать никнейм игрока'
    with open(
        path.join('db', 'minecraft.json'), 'r', encoding='utf8'
    ) as f:
        data = json.load(f)
    data[nick] = int(id)
    with open(
        path.join('db', 'minecraft.json'), 'w', encoding='utf8'
    ) as f:
        json.dump(
            data, f, indent=4, ensure_ascii=False, sort_keys=True
        )


def update_shop():
    current_shop = {}
    with open(
        path.join('db', 'shop_all.json'), 'r', encoding='utf8'
    ) as f:
        data = json.load(f)
    themes = []
    for theme in data:
        themes.append(theme)
    current_shop['theme'] = choice(themes)
    current_items = []
    all_items = list(data[current_shop['theme']].keys())
    while len(current_items) != 5:
        current_items.append(choice(list(all_items)))
    while len(set(current_items)) != len(current_items) \
            or len(current_items) < 5:
        current_items = list(set(current_items))
        current_items.append(choice(all_items))
    for item in current_items:
        current_shop[item] = data[current_shop['theme']][item]
    with open(
        path.join('db', 'shop_current.json'), 'w', encoding='utf8'
    ) as f:
        json.dump(
            current_shop, f, indent=4, ensure_ascii=False, sort_keys=True
        )


def get_shop():
    with open(
        path.join('db', 'shop_current.json'), 'r', encoding='utf8'
    ) as f:
        data = json.load(f)
    return data


def get_warns(id):
    id = str(id)
    with open(
        path.join('db', 'warns.json'), 'r', encoding='utf8'
    ) as f:
        data = json.load(f)
    if id in data:
        return data[id]
    else:
        with open(
            path.join('db', 'warns.json'), 'r', encoding='utf8'
        ) as f:
            data[id] = {}
            json.dump(
                data, f, indent=4, ensure_ascii=False, sort_keys=True
            )
        return {}


def set_warn(id):
    id = str(id)
    with open(
        path.join('db', 'warns.json'), 'r', encoding='utf8'
    ) as f:
        data = json.load(f)
    if id in data:
        if len(data[id]) == settings('max_warns')-1:
            data[id] = {}
            warns = settings('max_warns')
        else:
            data[id][str(len(data[id])+1)] = time()
            warns = len(data[id])
    with open(
        path.join('db', 'warns.json'), 'r', encoding='utf8'
    ) as f:
        json.dump(
            data, f, indent=4, ensure_ascii=False, sort_keys=True
        )
    return warns
