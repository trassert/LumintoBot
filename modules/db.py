import json, orjson
import aiomysql

from typing import Dict
from loguru import logger
from datetime import datetime, timedelta
from os import path, listdir, replace, makedirs, remove
from time import time
from random import choice, randint
from collections import defaultdict

from . import config
from .get_theme import weighted_choice
from .pathes import *


def database(key, value=None, delete=None, log=True):
    "Изменить/получить ключ из настроек"
    if value is not None:
        if log:
            logger.info(f"Значение {key} теперь {value}")
        try:
            with open(data_path, "rb") as f:
                load = orjson.loads(f.read())
            with open(data_path, "w", encoding="utf-8") as f:
                load[key] = value
                load = dict(sorted(load.items()))
                return json.dump(load, f, indent=4, ensure_ascii=False, sort_keys=True)
        except FileNotFoundError:
            logger.error("Файл не найден")
            with open(data_path, "w", encoding="utf-8") as f:
                load = {}
                load[key] = value
                return json.dump(load, f, indent=4, sort_keys=True)
        except json.decoder.JSONDecodeError:
            logger.error("Ошибка при чтении файла")
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)
            return None
    elif delete is not None:
        if log:
            logger.info(f"Удаляю ключ: {key}")
        with open(data_path, "rb") as f:
            load = orjson.loads(f.read())
        with open(data_path, "w", encoding="utf-8") as f:
            if key in load:
                del load[key]
            return json.dump(load, f, indent=4, ensure_ascii=False, sort_keys=True)
    else:
        if log:
            logger.info(f"Получаю ключ: {key}")
        try:
            with open(data_path, "rb") as f:
                load = orjson.loads(f.read())
                return load.get(key)
        except json.decoder.JSONDecodeError:
            logger.error("Ошибка при чтении файла")
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)
            return None
        except FileNotFoundError:
            logger.error("Файл не найден")
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)
            return None


def get_money(id):
    id = str(id)
    with open(money_path, "rb") as f:
        load = orjson.loads(f.read())
        if id in load:
            return load[id]

    with open(money_path, "w", encoding="utf8") as f:
        load[id] = 0
        json.dump(load, f, indent=4, ensure_ascii=False, sort_keys=True)
        return 0


def get_all_money():
    "Получить все деньги"
    with open(money_path, "rb") as f:
        load = orjson.loads(f.read())
        return sum(load.values())


def add_money(id, count):
    id = str(id)
    with open(money_path, "rb") as f:
        load = orjson.loads(f.read())
        if id in load:
            old = load[id]
            load[id] = load[id] + count
        else:
            old = 0
            load[id] = count

    if load[id] < 0:
        load[id] = 0
    with open(money_path, "w", encoding="utf8") as f:
        json.dump(load, f, indent=4, ensure_ascii=False, sort_keys=True)
        logger.info(f"Изменён баланс {id} ({old} -> {load[id]})")
        return load[id]


def update_shop():
    "Обновляет магазин"
    "Возвращает тему магазина"
    with open(path.join("db", "shop_current.json"), "r", encoding="utf8") as f:
        last_theme = orjson.loads(f.read())["theme"]
    current_shop = {}
    with open(path.join("db", "shop_all.json"), "rb") as f:
        load = orjson.loads(f.read())
    themes = []
    for theme in load:
        themes.append(theme)
    current_shop["theme"] = weighted_choice(themes, database("shop_weight"))
    while current_shop["theme"] is last_theme:
        current_shop["theme"] = weighted_choice(themes, database("shop_weight"))
    current_items = []
    all_items = list(load[current_shop["theme"]].keys())
    while len(set(current_items)) != len(current_items) or len(current_items) < 5:
        current_items = list(set(current_items))
        current_items.append(choice(all_items))
    for item in current_items:
        current_shop[item] = load[current_shop["theme"]][item]
    with open(path.join("db", "shop_current.json"), "w", encoding="utf8") as f:
        json.dump(current_shop, f, indent=4, ensure_ascii=False, sort_keys=True)
    return current_shop["theme"]


def get_shop():
    with open(path.join("db", "shop_current.json"), "rb") as f:
        load = orjson.loads(f.read())
    return load


def ready_to_mine(id: str) -> bool:
    id = str(id)
    with open(mine_path, "rb") as f:
        data = orjson.loads(f.read())
    if (id not in data) or (
        int(time()) - data.get(id, int(time())) > config.coofs.MineWait
    ):
        data[id] = int(time())
        with open(mine_path, "w", encoding="utf8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=True)
        return True
    return False


class roles:
    BLACKLIST = -1
    USER = 0
    VIP = 1
    INTERN = 2
    MODER = 3
    ADMIN = 4
    OWNER = 5

    def get(self, id: str) -> int:
        "Получить роль пользователя (U0, если не найдено)"
        id = str(id)
        with open(roles_path, "rb") as f:
            return orjson.loads(f.read()).get(str(id), self.USER)

    def set(self, id: str, role: int) -> bool:
        "Установить роль пользователя"
        id = str(id)
        role = int(role)
        with open(roles_path, "rb") as f:
            data = orjson.loads(f.read())
        data[id] = role
        with open(roles_path, "w", encoding="utf-8") as f:
            json.dump(
                dict(sorted(data.items(), key=lambda x: (-x[1], x[0]))),
                f,
                indent=4,
                ensure_ascii=False,
            )


class crocodile_stat:
    def __init__(self, id=False):
        if id:
            self.id = str(id)

    def get(self):
        with open(crocodile_stats_path, "rb") as f:
            load = orjson.loads(f.read())
        if self.id in load:
            return load[self.id]
        else:
            with open(
                path.join("db", "crocodile_stat.json"), "rb"
            ) as f:
                load[self.id] = 0
                json.dump(load, f, indent=4, ensure_ascii=False, sort_keys=True)
            return 0

    def add(self):
        with open(crocodile_stats_path, "rb") as f:
            load = orjson.loads(f.read())
        if self.id in load:
            load[self.id] += 1
        else:
            load[self.id] = 1
        with open(crocodile_stats_path, "w", encoding="utf8") as f:
            json.dump(load, f, indent=4, ensure_ascii=False, sort_keys=True)

    def get_all(self=False):
        with open(crocodile_stats_path, "rb") as f:
            load = orjson.loads(f.read())
        return dict(sorted(load.items(), key=lambda item: item[1], reverse=True))


class nicks:
    def __init__(self, nick=None, id=None):
        self.nick = nick
        self.id = id

    def get(self, if_nothing=None) -> str:
        if self.nick:
            "Получить id игрока по нику"
            with open(nick_path, "rb") as f:
                load = orjson.loads(f.read())
                if self.nick in load:
                    return load[self.nick]
                return if_nothing
        elif self.id:
            "Получить ник по id"
            with open(nick_path, "rb") as f:
                load = orjson.loads(f.read())
                for key, value in load.items():
                    if value == self.id:
                        return key
                return if_nothing
        else:
            raise TypeError("Нужен ник или id!")

    def get_all(self):
        with open(nick_path, "rb") as f:
            load = orjson.loads(f.read())
            return dict(sorted(load.items()))

    def link(self):
        with open(nick_path, "rb") as f:
            load = orjson.loads(f.read())
        for key, value in load.items():
            if value == self.id:
                del load[key]
                break
        load[self.nick] = int(self.id)
        with open(nick_path, "w", encoding="utf8") as f:
            json.dump(load, f, indent=4, ensure_ascii=False, sort_keys=True)
        return True


class statistic:
    def __init__(self, days=1):
        self.days = days

    def get(self, nick, all_days=False, data=False):
        "Выдаст статистику по заданным аргументам"
        now = datetime.now().strftime("%Y.%m.%d")

        # Если нет файла
        if not path.exists(path.join(stats_path, f"{nick}.json")):
            with open(path.join(stats_path, f"{nick}.json"), "w", encoding="utf8") as f:
                stats = {}
                stats[now] = 0
                json.dump(stats, f, indent=4, ensure_ascii=False, sort_keys=True)
                return 0

        # Если есть файл
        with open(path.join(stats_path, f"{nick}.json"), "rb") as f:
            stats = orjson.loads(f.read())
            if all_days:
                return sum(stats.values()) or 0
            dates = list(stats.keys())
            dates.sort(reverse=True)
            start_date = datetime.now() - timedelta(days=self.days)
            filtered_data = {
                date: value
                for date, value in stats.items()
                if datetime.strptime(date, "%Y.%m.%d") >= start_date
            }
            if data:
                return filtered_data
            return sum(filtered_data.values()) or 0

    def get_all(self, all_days=False):
        "Выдаст игрок: сообщения за days дней"
        "Если all_days указан, выдаст все дни"
        data = {}
        for file in listdir(stats_path):
            nick = file.replace(".json", "")
            nick_stat = self.get(nick, True if all_days else False)
            if nick_stat > 1:
                data[nick] = nick_stat
        return sorted(data.items(), key=lambda item: item[1], reverse=True)

    def add(nick, date=None):
        "+1 в статистику игрока"
        "datе указывать при перерасчёте и т.д."

        now = date if date else datetime.now().strftime("%Y.%m.%d")

        # Если нет файла
        if not path.exists(path.join(stats_path, f"{nick}.json")):
            with open(path.join(stats_path, f"{nick}.json"), "w", encoding="utf8") as f:
                stats = {}
                stats[now] = 1
                json.dump(stats, f, indent=4, ensure_ascii=False, sort_keys=True)

        # Если есть файл
        with open(path.join(stats_path, f"{nick}.json"), "rb") as f:
            stats = orjson.loads(f.read())
            if now in stats:
                stats[now] = stats[now] + 1
            else:
                stats[now] = 1
        with open(path.join(stats_path, f"{nick}.json"), "w", encoding="utf8") as f:
            json.dump(stats, f, indent=4, ensure_ascii=False, sort_keys=True)

    def get_raw(self) -> dict[str, int]:
        "Выдаёт {дата: сообщения} от всех"
        "Если days не указан, выдаст все"
        totals = defaultdict(int)
        for json_file in listdir(stats_path):
            try:
                with open(path.join(stats_path, json_file), "rb") as f:
                    data = orjson.loads(f.read())
                    for date, count in data.items():
                        totals[date] += count
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"Ошибка при чтении файла - {json_file}")
                continue
        if self.days != 1:
            start_date = datetime.now() - timedelta(days=self.days)
            return {
                date: value
                for date, value in totals.items()
                if datetime.strptime(date, "%Y.%m.%d") >= start_date
            }
        return dict(sorted(totals.items(), key=lambda item: item[0]))


class ticket:
    def get(id):
        id = str(id)
        "Получить чек по id"
        if path.exists(tickets_path):
            with open(tickets_path, "rb") as f:
                data = orjson.loads(f.read())
                if id in data:
                    return data[id]
                return None
        else:
            with open(tickets_path, "w", encoding="utf8") as f:
                json.dump({}, f, indent=4, ensure_ascii=False, sort_keys=True)
            return None

    def add(author, value):
        if path.exists(tickets_path):
            with open(tickets_path, "rb") as f:
                data = orjson.loads(f.read())
            with open(tickets_path, "w", encoding="utf8") as f:
                random_id = randint(1000, 9999)
                while random_id in data:
                    random_id = randint(1000, 9999)
                data[str(random_id)] = {
                    "author": int(author),
                    "value": int(value),
                }
                json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=True)
                logger
                return random_id
        else:
            with open(tickets_path, "w", encoding="utf8") as f:
                random_id = str(randint(1000, 9999))
                json.dump(
                    {random_id: {"author": int(author), "value": int(value)}},
                    f,
                    indent=4,
                    ensure_ascii=False,
                    sort_keys=True,
                )
            return random_id

    def delete(id):
        with open(tickets_path, "rb") as f:
            data = orjson.loads(f.read())
            if id not in data:
                return None
            else:
                del data[id]
        with open(tickets_path, "w", encoding="utf8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=True)
            return True


class state:
    def __init__(self, name):
        self.name: str = name
        self._info()

    def _info(self):
        with open(path.join(states_path, f"{self.name}.json"), "rb") as f:
            all = orjson.loads(f.read())
        self.all = all
        self.price = all["price"]
        self.enter = all["enter"]
        self.desc = all["desc"]
        self.players = all["players"]
        self.type = all["type"]
        self.date = all["date"]
        self.author = all["author"]
        self.coordinates = all["coordinates"]
        self.money = all["money"]

    def change(self, key, value):
        with open(
            path.join(states_path, f"{self.name}.json"), "w", encoding="utf8"
        ) as f:
            self.all[key] = value
            json.dump(self.all, f, indent=4, ensure_ascii=False, sort_keys=True)

    def rename(self, new_name: str):
        if path.exists(path.join(states_path, f"{new_name}.json")):
            return False
        else:
            replace(
                path.join(states_path, f"{self.name}.json"),
                path.join(states_path, f"{new_name}.json"),
            )
            self.name = new_name
            self._info()


class states:
    def add(name, author):
        if path.exists(path.join(states_path, f"{name}.json")):
            return
        with open(path.join(states_path, f"{name}.json"), "w", encoding="utf8") as f:
            json.dump(
                {
                    "price": 0,
                    "enter": True,
                    "desc": "Пусто",
                    "players": [],
                    "type": 0,
                    "date": datetime.now().strftime("%Y.%m.%d"),
                    "money": 0,
                    "author": author,
                    "coordinates": "Не найдено",
                },
                f,
                indent=4,
                ensure_ascii=False,
                sort_keys=True,
            )
            return True

    def check(name):
        if path.exists(path.join(states_path, f"{name}.json")):
            return True
        return False

    def get_all(sortedby="players"):
        """Выдаёт все государства, сортированные по sortedby

        Args:
            sortedby (str, optional): Автоматическая сортировка. По умолчанию "players".

        Returns:
            dict: Все государства сортированные в реверсе
        """
        all = {}
        for file in listdir(states_path):
            with open(path.join(states_path, file), "rb") as f:
                try:
                    all[file.replace(".json", "")] = orjson.loads(f.read())
                except json.decoder.JSONDecodeError:
                    logger.error(f"Не удалось просмотреть гос-во {file}")
        return dict(
            sorted(all.items(), key=lambda item: len(item[1][sortedby]), reverse=True)
        )

    def if_author(id: int):
        for file in listdir(states_path):
            with open(path.join(states_path, file), "rb") as f:
                if orjson.loads(f.read())["author"] == id:
                    return file.replace(".json", "")
        return False

    def if_player(id: int):
        for file in listdir(states_path):
            with open(path.join(states_path, file), "rb") as f:
                for player in orjson.loads(f.read())["players"]:
                    if player == id:
                        return file.replace(".json", "")
        return False

    def find(name: str) -> bool:
        if path.exists(path.join(states_path, f"{name}.json")):
            return True
        return False

    def remove(name: str) -> bool:
        state = path.join(states_path, f"{name}.json")
        if path.exists(state):
            replace(state, path.join(old_states_path, f"{name}.json"))
            return True
        return False


class Mysql:
    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        db: str,
        table_name: str,
        port: int = 3306,
        minsize: int = 1,
        maxsize: int = 10,
    ):
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self.port = port
        self.minsize = minsize
        self.maxsize = maxsize
        self.pool = None
        self.table_name = table_name

    async def initialize(self):
        self.pool = await aiomysql.create_pool(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.db,
            minsize=self.minsize,
            maxsize=self.maxsize,
        )

    async def get_by_id(self, id: int) -> Dict[str, int]:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                SELECT wins_casino, lose_moneys_in_casino 
                FROM {self.table_name} 
                WHERE id = %s
                """,
                    (id,),
                )
                result = await cur.fetchone()
                if result:
                    return {"wins_casino": result[0], "lose_moneys_in_casino": result[1]}
                return {"wins_casino": 0, "lose_moneys_in_casino": 0}

    async def get_all(self) -> Dict[int, Dict[str, int]]:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                SELECT id, wins_casino, lose_moneys_in_casino 
                FROM {self.table_name}
                """
                )
                results = await cur.fetchall()
                return {
                    row[0]: {"wins_casino": row[1], "lose_moneys_in_casino": row[2]}
                    for row in results
                }

    async def add_win(self, id: int):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                INSERT INTO {self.table_name} (id, wins_casino, lose_moneys_in_casino)
                VALUES (%s, 1, 0)
                ON DUPLICATE KEY UPDATE wins_casino = wins_casino + 1
                """,
                    (id,),
                )
                await conn.commit()

    async def add_lose_money(self, id: int, amount: int = 1):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                INSERT INTO {self.table_name} (id, wins_casino, lose_moneys_in_casino)
                VALUES (%s, 0, %s)
                ON DUPLICATE KEY UPDATE lose_moneys_in_casino = lose_moneys_in_casino + %s
                """,
                    (id, amount, amount),
                )
                await conn.commit()


Users = Mysql(
    host=config.tokens.mysql_users.host,
    user=config.tokens.mysql_users.user,
    password=config.tokens.mysql_users.password,
    db=config.tokens.mysql_users.database,
    table_name=config.tokens.mysql_users.table
)


class Notes:
    def __init__(self, storage_dir=notes_path):
        self.storage_dir = storage_dir
        makedirs(storage_dir, exist_ok=True)

    def _get_file_path(self, name):
        """Возвращает путь к файлу заметки."""
        return path.join(self.storage_dir, f"{name}.txt")

    def get(self, name: str):
        """Получить заметку по имени. Возвращает текст или None."""
        file_path = self._get_file_path(name.lower())
        if not path.exists(file_path):
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def create(self, name: str, text: str):
        """Создать новую заметку. Возвращает True при успехе, False если уже существует."""
        file_path = self._get_file_path(name.lower())
        if path.exists(file_path):
            return False
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        return True

    def remove(self, name: str):
        """Удалить заметку. Возвращает True при успехе, False если не существует."""
        file_path = self._get_file_path(name.lower())
        if not path.exists(file_path):
            return False
        remove(file_path)
        return True

    def get_all(self) -> list[str]:
        if path.exists(self.storage_dir):
            return [
                path.splitext(f)[0]
                for f in listdir(self.storage_dir)
                if path.isfile(path.join(self.storage_dir, f))
            ]
        return []