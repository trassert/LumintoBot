import json

from loguru import logger
from datetime import datetime, timedelta
from os import path, listdir
from random import choice, randint
from .random import weighted_choice

nick_path = path.join('db', 'minecraft.json')
stats_path = path.join('db', 'chat_stats')
tickets_path = path.join('db', 'tickets.json')


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
    with open(
        path.join('db', 'shop_current.json'), 'r', encoding='utf8'
    ) as f:
        last_theme = json.load(f)['theme']
    current_shop = {}
    with open(
        path.join('db', 'shop_all.json'), 'r', encoding='utf8'
    ) as f:
        load = json.load(f)
    themes = []
    for theme in load:
        themes.append(theme)
    current_shop['theme'] = weighted_choice(themes, setting('shop_weight'))
    while current_shop['theme'] is last_theme:
        current_shop['theme'] = weighted_choice(themes, setting('shop_weight'))
    current_items = []
    all_items = list(load[current_shop['theme']].keys())
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
        for key, value in load.items():
            if value == self.id:
                del load[key]
                break
        load[self.nick] = int(self.id)
        with open(nick_path, 'w', encoding='utf8') as f:
            json.dump(
                load, f, indent=4, ensure_ascii=False, sort_keys=True
            )
        return True


class statistic:
    def __init__(self, days=1):
        self.days = days

    def get(self, nick, all_days=False):
        'Получить статистику по заданным аргументам'
        now = datetime.now().strftime("%Y.%m.%d")

        # Если нет файла
        if not path.exists(path.join(stats_path, f'{nick}.json')):
            with open(
                path.join(stats_path, f'{nick}.json'), 'w', encoding='utf8'
            ) as f:
                stats = {}
                stats[now] = 0
                json.dump(
                    stats, f, indent=4, ensure_ascii=False, sort_keys=True
                )
                return 0

        # Если есть файл
        with open(
            path.join(stats_path, f'{nick}.json'), 'r', encoding='utf8'
        ) as f:
            stats = json.load(f)
            if all_days:
                return sum(stats.values()) or 0
            dates = list(stats.keys())
            dates.sort(reverse=True)
            start_date = datetime.now() - timedelta(days=self.days)
            filtered_data = {
                date: value for date, value in stats.items()
                if datetime.strptime(date, '%Y.%m.%d') >= start_date
            }
            return sum(filtered_data.values()) or 0

    def get_all(self, all_days=False):
        data = {}
        for file in listdir(stats_path):
            nick = file.replace('.json', '')
            nick_stat = self.get(nick, True if all_days else False)
            if nick_stat > 1:
                data[nick] = nick_stat
        return sorted(data.items(), key=lambda item: item[1], reverse=True)

    def add(nick):
        '+1 в статистику игрока'
        now = datetime.now().strftime("%Y.%m.%d")

        # Если нет файла
        if not path.exists(path.join(stats_path, f'{nick}.json')):
            with open(
                path.join(stats_path, f'{nick}.json'), 'w', encoding='utf8'
            ) as f:
                stats = {}
                stats[now] = 1
                json.dump(
                    stats, f, indent=4, ensure_ascii=False, sort_keys=True
                )

        # Если есть файл
        with open(
            path.join(stats_path, f'{nick}.json'), 'r', encoding='utf8'
        ) as f:
            stats = json.load(f)
            if now in stats:
                stats[now] = stats[now] + 1
            else:
                stats[now] = 1
        with open(
            path.join(stats_path, f'{nick}.json'), 'w', encoding='utf8'
        ) as f:
            json.dump(
                stats, f, indent=4, ensure_ascii=False, sort_keys=True
            )


class ticket:
    def get(id):
        id = str(id)
        'Получить чек по id'
        if path.exists(tickets_path):
            with open(
                tickets_path, 'r', encoding='utf8'
            ) as f:
                data = json.load(f)
                if id in data:
                    return data[id]
                return None
        else:
            with open(
                tickets_path, 'w', encoding='utf8'
            ) as f:
                json.dump({}, f, indent=4, ensure_ascii=False, sort_keys=True)
            return None

    def add(author, value):
        if path.exists(tickets_path):
            with open(
                tickets_path, 'r', encoding='utf8'
            ) as f:
                data = json.load(f)
            with open(
                tickets_path, 'w', encoding='utf8'
            ) as f:
                random_id = randint(1000, 9999)
                while random_id in data:
                    random_id = randint(1000, 9999)
                data[str(random_id)] = {
                    'author': int(author),
                    'value': int(value),
                }
                json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=True)
                logger
                return random_id
        else:
            with open(
                tickets_path, 'w', encoding='utf8'
            ) as f:
                random_id = str(randint(1000, 9999))
                json.dump(
                    {
                        random_id: {
                            'author': int(author),
                            'value': int(value)
                        }
                    },
                    f,
                    indent=4,
                    ensure_ascii=False,
                    sort_keys=True
                )
            return random_id

    def delete(id):
        with open(
            tickets_path, 'r', encoding='utf8'
        ) as f:
            data = json.load(f)
            if id not in data:
                return None
            else:
                del data[id]
        with open(
            tickets_path, 'w', encoding='utf8'
        ) as f:
            json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=True)
            return True
