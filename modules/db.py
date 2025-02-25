import json
import logging

from os import path
from random import choice
from .random import weighted_choice

logger = logging.getLogger(__name__)

nick_path = path.join('db', 'minecraft.json')

def setting(key, value=None, delete=None, log=True):
    "Изменить/получить ключ из настроек"
    if value is not None:
        if log:
            logger.info(f"Значение {key} теперь {value}")
        try:
            with open(
                path.join('db', 'data.json'), "r", encoding="utf-8"
            ) as f:
                load = json.load(f)
            with open(
                path.join('db', 'data.json'), "w", encoding="utf-8"
            ) as f:
                load[key] = value
                load = dict(sorted(load.items()))
                return json.dump(
                    load, f, indent=4, ensure_ascii=False, sort_keys=True
                    )
        except FileNotFoundError:
            logger.error("Файл не найден")
            with open(
                path.join('db', 'data.json'), "w", encoding="utf-8"
            ) as f:
                load = {}
                load[key] = value
                return json.dump(load, f, indent=4, sort_keys=True)
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
            load = json.load(f)
        with open(
            path.join('db', 'data.json'), "w", encoding="utf-8"
        ) as f:
            if key in load:
                del load[key]
            return json.dump(
                load, f, indent=4, ensure_ascii=False, sort_keys=True
                )
    else:
        if log:
            logger.info(f"Получаю ключ: {key}")
        try:
            with open(
                path.join('db', 'data.json'), "r", encoding="utf-8"
            ) as f:
                load = json.load(f)
                return load.get(key)
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


def get_money(id):
    id = str(id)
    with open(
        path.join('db', 'money.json'), 'r', encoding='utf8'
    ) as f:
        load = json.load(f)
        if id in load:
            return load[id]

    with open(
        path.join('db', 'money.json'), 'w', encoding='utf8'
    ) as f:
        load[id] = 0
        json.dump(
            load, f, indent=4, ensure_ascii=False, sort_keys=True
        )
        return 0


def get_all_money():
    'Получить все деньги'
    with open(
        path.join('db', 'money.json'), 'r', encoding='utf8'
    ) as f:
        load = json.load(f)
        return sum(load.values())


def add_money(id, count):
    id = str(id)
    with open(
        path.join('db', 'money.json'), 'r', encoding='utf8'
    ) as f:
        load = json.load(f)
        if id in load:
            old = load[id]
            load[id] = load[id] + count
        else:
            old = 0
            load[id] = count

    if load[id] < 0:
        load[id] = 0
    with open(
        path.join('db', 'money.json'), 'w', encoding='utf8'
    ) as f:
        json.dump(
            load, f, indent=4, ensure_ascii=False, sort_keys=True
        )
        logger.info(f'Изменён баланс {id} ({old} -> {load[id]})')
        return load[id]


def update_shop():
    'Обновляет магазин'
    'Возвращает тему магазина'
    current_shop = {}
    with open(
        path.join('db', 'shop_all.json'), 'r', encoding='utf8'
    ) as f:
        load = json.load(f)
    themes = []
    for theme in load:
        themes.append(theme)
    current_shop['theme'] = weighted_choice(themes, setting('shop_weight'))
    current_items = []
    all_items = list(load[current_shop['theme']].keys())
    while len(current_items) != 5:
        current_items.append(choice(list(all_items)))
    while len(set(current_items)) != len(current_items) \
            or len(current_items) < 5:
        current_items = list(set(current_items))
        current_items.append(choice(all_items))
    for item in current_items:
        current_shop[item] = load[current_shop['theme']][item]
    with open(
        path.join('db', 'shop_current.json'), 'w', encoding='utf8'
    ) as f:
        json.dump(
            current_shop, f, indent=4, ensure_ascii=False, sort_keys=True
        )
    return current_shop['theme']


def get_shop():
    with open(
        path.join('db', 'shop_current.json'), 'r', encoding='utf8'
    ) as f:
        load = json.load(f)
    return load


class crocodile_stat:
    def __init__(self, id=False):
        if id:
            self.id = str(id)

    def get(self):
        with open(
            path.join('db', 'crocodile_stat.json'), 'r', encoding='utf8'
        ) as f:
            load = json.load(f)
        if self.id in load:
            return load[self.id]
        else:
            with open(
                path.join('db', 'crocodile_stat.json'), 'r', encoding='utf8'
            ) as f:
                load[self.id] = 0
                json.dump(
                    load, f, indent=4, ensure_ascii=False, sort_keys=True
                )
            return 0

    def add(self):
        with open(
            path.join('db', 'crocodile_stat.json'), 'r', encoding='utf8'
        ) as f:
            load = json.load(f)
        if self.id in load:
            load[self.id] += 1
        else:
            load[self.id] = 1
        with open(
            path.join('db', 'crocodile_stat.json'), 'w', encoding='utf8'
        ) as f:
            json.dump(
                load, f, indent=4, ensure_ascii=False, sort_keys=True
            )

    def get_all(self=False):
        with open(
            path.join('db', 'crocodile_stat.json'), 'r', encoding='utf8'
        ) as f:
            load = json.load(f)
        return dict(
            sorted(load.items(), key=lambda item: item[1], reverse=True)
        )

class nicks:
    def __init__(self, nick=None, id=None):
        self.nick = nick
        self.id = id
    def get(self):
        if self.nick:
            'Получить id игрока по нику'
            with open(nick_path, 'r', encoding='utf8') as f:
                load = json.load(f)
                if self.nick in load:
                    return load[self.nick]
                return None
        elif self.id:
            'Получить ник по id'
            with open(nick_path, 'r', encoding='utf8') as f:
                load = json.load(f)
                for key, value in load.items():
                    if value == self.id:
                        return key
                return None
        else:
            raise TypeError('Нужен ник или id!')
    def get_all(self):
        with open(nick_path, 'r', encoding='utf8') as f:
            load = json.load(f)
            return dict(sorted(load.items()))
    def link(self):
        with open(nick_path, 'r', encoding='utf8') as f:
            load = json.load(f)
        load[self.nick] = int(self.id)
        with open(nick_path, 'w', encoding='utf8') as f:
            json.dump(
                load, f, indent=4, ensure_ascii=False, sort_keys=True
            )
        return True