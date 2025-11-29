from collections import defaultdict
from datetime import datetime, timedelta
from json import JSONDecodeError
from os import listdir, makedirs, path, remove, replace
from random import choice, randint
from time import time

import aiofiles
import asyncmy
import orjson
from loguru import logger

from . import config, formatter, pathes
from .get_theme import weighted_choice

logger.info(f"Загружен модуль {__name__}!")


def database(key, value=None, delete=None, log=True):
    """Изменить/получить ключ из настроек"""
    if value is not None:
        if log:
            logger.info(f"Значение {key} теперь {value}")
        try:
            with open(pathes.data, "rb") as f:
                load = orjson.loads(f.read())
            with open(pathes.data, "wb") as f:
                load[key] = value
                load = dict(sorted(load.items()))
                return f.write(orjson.dumps(load, option=orjson.OPT_INDENT_2))
        except FileNotFoundError:
            logger.error("Файл не найден")
            with open(pathes.data, "wb") as f:
                load = {}
                load[key] = value
                return f.write(orjson.dumps(load, option=orjson.OPT_INDENT_2))
        except JSONDecodeError:
            logger.error("Ошибка при чтении файла")
            with open(pathes.data, "wb") as f:
                f.write(orjson.loads({}, option=orjson.OPT_INDENT_2))
            return None
    elif delete is not None:
        if log:
            logger.info(f"Удаляю ключ: {key}")
        with open(pathes.data, "rb") as f:
            load = orjson.loads(f.read())
        with open(pathes.data, "wb") as f:
            if key in load:
                del load[key]
            return f.write(orjson.dumps(load, option=orjson.OPT_INDENT_2))
    else:
        if log:
            logger.info(f"Получаю ключ: {key}")
        try:
            with open(pathes.data, "rb") as f:
                load = orjson.loads(f.read())
                return load.get(key)
        except JSONDecodeError:
            logger.error("Ошибка при чтении файла")
            with open(pathes.data, "wb") as f:
                f.write(orjson.loads({}, option=orjson.OPT_INDENT_2))
            return None
        except FileNotFoundError:
            logger.error("Файл не найден")
            with open(pathes.data, "wb") as f:
                f.write(orjson.loads({}, option=orjson.OPT_INDENT_2))
            return None


async def get_money(id):
    id = str(id)
    async with aiofiles.open(pathes.money, "rb") as f:
        load = orjson.loads(await f.read())
        if id in load:
            return load[id]

    async with aiofiles.open(pathes.money, "wb") as f:
        load[id] = 0
        await f.write(orjson.dumps(load, option=orjson.OPT_INDENT_2))
        return 0


def get_all_money():
    """Получить все деньги"""
    with open(pathes.money, "rb") as f:
        load = orjson.loads(f.read())
        return sum(load.values())


def add_money(id, count):
    id = str(id)
    with open(pathes.money, "rb") as f:
        load = orjson.loads(f.read())
        if id in load:
            old = load[id]
            load[id] = load[id] + count
        else:
            old = 0
            load[id] = count

    load[id] = max(load[id], 0)
    with open(pathes.money, "wb") as f:
        f.write(orjson.dumps(load, option=orjson.OPT_INDENT_2))
        logger.info(f"Изменён баланс {id} ({old} -> {load[id]})")
        return load[id]


def update_shop():
    """Обновляет магазин, возвращая новую тему."""
    with open(pathes.shopc, "rb") as f:
        last_theme = orjson.loads(f.read()).get("theme")
    with open(pathes.shop, "rb") as f:
        all_themes = orjson.loads(f.read())
    if not all_themes:
        logger.exception("Файл shop_all.json пуст или не содержит тем.")
    theme_names = list(all_themes.keys())
    if not theme_names:
        logger.exception("Нет доступных тем в shop_all.json")
    new_theme = last_theme
    while new_theme == last_theme:
        new_theme = weighted_choice(theme_names, database("shop_weight"))
    theme_items = all_themes[new_theme]
    item_names = list(theme_items.keys())
    if len(item_names) < 5:
        logger.exception(
            f"В теме '{new_theme}' недостаточно предметов (минимум 5, найдено {len(item_names)})"
        )
    selected_items = []
    while len(selected_items) < 5:
        item = choice(item_names)
        if item not in selected_items:
            selected_items.append(item)
    current_shop = {"theme": new_theme}
    for item in selected_items:
        item_data = theme_items[item].copy()
        price = item_data.get("price")
        if isinstance(price, list) and len(price) == 2:
            min_p, max_p = price
            item_data["price"] = randint(min_p, max_p)
        elif isinstance(price, (int, float)):
            pass
        else:
            logger.exception(
                f"Некорректный формат цены для предмета '{item}': {price}"
            )
        current_shop[item] = item_data
    with open(pathes.shopc, "wb") as f:
        f.write(orjson.dumps(current_shop, option=orjson.OPT_INDENT_2))
    return new_theme


def get_shop():
    with open(path.join("db", "shop_current.json"), "rb") as f:
        load = orjson.loads(f.read())
    return load


def ready_to_mine(id: str) -> bool:
    id = str(id)
    with open(pathes.mine, "rb") as f:
        data = orjson.loads(f.read())
    if (id not in data) or (
        int(time()) - data.get(id, int(time())) > config.coofs.MineWait
    ):
        data[id] = int(time())
        with open(pathes.mine, "wb") as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
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
        """Получить роль пользователя (U0, если не найдено)"""
        id = str(id)
        with open(pathes.roles, "rb") as f:
            return orjson.loads(f.read()).get(str(id), self.USER)

    def set(self, id: str, role: int) -> bool:
        """Установить роль пользователя"""
        id = str(id)
        role = int(role)
        with open(pathes.roles, "rb") as f:
            data = orjson.loads(f.read())
        data[id] = role
        with open(pathes.roles, "wb") as f:
            f.write(
                orjson.dumps(
                    dict(sorted(data.items(), key=lambda x: (-x[1], x[0]))),
                    option=orjson.OPT_INDENT_2,
                ),
            )


class crocodile_stat:
    def __init__(self, id=False):
        if id:
            self.id = str(id)

    def get(self):
        with open(pathes.crocostat, "rb") as f:
            load = orjson.loads(f.read())
        if self.id in load:
            return load[self.id]
        with open(pathes.crocostat, "wb") as f:
            load[self.id] = 0
            f.write(orjson.dumps(load, option=orjson.OPT_SORT_KEYS))
        return 0

    def add(self):
        with open(pathes.crocostat, "rb") as f:
            load = orjson.loads(f.read())
        if self.id in load:
            load[self.id] += 1
        else:
            load[self.id] = 1
        with open(pathes.crocostat, "wb") as f:
            f.write(orjson.dumps(load, option=orjson.OPT_SORT_KEYS))

    def get_all(self=False):
        with open(pathes.crocostat, "rb") as f:
            load = orjson.loads(f.read())
        return dict(
            sorted(load.items(), key=lambda item: item[1], reverse=True),
        )


class nicks:
    def __init__(self, nick=None, id=None):
        self.nick = nick
        self.id = id

    def get(self, if_nothing=None) -> str:
        if self.nick:
            "Получить id игрока по нику"
            with open(pathes.nick, "rb") as f:
                load = orjson.loads(f.read())
                if self.nick in load:
                    return load[self.nick]
                return if_nothing
        elif self.id:
            "Получить ник по id"
            with open(pathes.nick, "rb") as f:
                load = orjson.loads(f.read())
                for key, value in load.items():
                    if value == self.id:
                        return key
                return if_nothing
        else:
            raise TypeError("Нужен ник или id!")

    def get_all(self):
        with open(pathes.nick, "rb") as f:
            load = orjson.loads(f.read())
            return dict(sorted(load.items()))

    def link(self):
        with open(pathes.nick, "rb") as f:
            load = orjson.loads(f.read())
        for key, value in load.items():
            if value == self.id:
                del load[key]
                break
        load[self.nick] = int(self.id)
        with open(pathes.nick, "wb") as f:
            f.write(orjson.dumps(load, option=orjson.OPT_INDENT_2))
        return True


class statistic:
    def __init__(self, days=1):
        self.days = days

    def get(self, nick, all_days=False, data=False):
        """Выдаст статистику по заданным аргументам"""
        now = datetime.now().strftime("%Y.%m.%d")

        # Если нет файла
        if not path.exists(path.join(pathes.stats, f"{nick}.json")):
            with open(path.join(pathes.stats, f"{nick}.json"), "wb") as f:
                stats = {}
                stats[now] = 0
                f.write(orjson.dumps(stats, option=orjson.OPT_SORT_KEYS))
                return 0

        # Если есть файл
        with open(path.join(pathes.stats, f"{nick}.json"), "rb") as f:
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
        """Выдаст игрок: сообщения за days дней"""
        "Если all_days указан, выдаст все дни"
        data = {}
        for file in listdir(pathes.stats):
            nick = file.replace(".json", "")
            nick_stat = self.get(nick, True if all_days else False)
            if nick_stat > 1:
                data[nick] = nick_stat
        return sorted(data.items(), key=lambda item: item[1], reverse=True)

    def add(nick, date=None):
        """+1 в статистику игрока"""
        "datе указывать при перерасчёте и т.д."

        now = date if date else datetime.now().strftime("%Y.%m.%d")

        # Если нет файла
        if not path.exists(path.join(pathes.stats, f"{nick}.json")):
            with open(path.join(pathes.stats, f"{nick}.json"), "wb") as f:
                stats = {}
                stats[now] = 1
                f.write(orjson.dumps(stats, option=orjson.OPT_SORT_KEYS))

        # Если есть файл
        with open(path.join(pathes.stats, f"{nick}.json"), "rb") as f:
            stats = orjson.loads(f.read())
            if now in stats:
                stats[now] = stats[now] + 1
            else:
                stats[now] = 1
        with open(path.join(pathes.stats, f"{nick}.json"), "wb") as f:
            f.write(orjson.dumps(stats, option=orjson.OPT_SORT_KEYS))

    def get_raw(self) -> dict[str, int]:
        """Выдаёт {дата: сообщения} от всех"""
        "Если days не указан, выдаст все"
        totals = defaultdict(int)
        for json_file in listdir(pathes.stats):
            try:
                with open(path.join(pathes.stats, json_file), "rb") as f:
                    data = orjson.loads(f.read())
                    for date, count in data.items():
                        totals[date] += count
            except (JSONDecodeError, UnicodeDecodeError):
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
        if path.exists(pathes.tickets):
            with open(pathes.tickets, "rb") as f:
                data = orjson.loads(f.read())
                if id in data:
                    return data[id]
                return None
        else:
            with open(pathes.tickets, "wb") as f:
                f.write(orjson.dumps({}))
            return None

    def add(author, value):
        if path.exists(pathes.tickets):
            with open(pathes.tickets, "rb") as f:
                data = orjson.loads(f.read())
            with open(pathes.tickets, "wb") as f:
                random_id = randint(1000, 9999)
                while random_id in data:
                    random_id = randint(1000, 9999)
                data[str(random_id)] = {
                    "author": int(author),
                    "value": int(value),
                }
                f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
                return random_id
        else:
            with open(pathes.tickets, "wb") as f:
                random_id = str(randint(1000, 9999))
                f.write(
                    orjson.dumps(
                        {
                            random_id: {
                                "author": int(author),
                                "value": int(value),
                            },
                        },
                        option=orjson.OPT_SORT_KEYS,
                    ),
                )
            return random_id

    def delete(id):
        with open(pathes.tickets, "rb") as f:
            data = orjson.loads(f.read())
            if id not in data:
                return None
            del data[id]
        with open(pathes.tickets, "wb") as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
            return True


class state:
    def __init__(self, name):
        self.name: str = name
        self._info()

    def _info(self):
        with open(path.join(pathes.states, f"{self.name}.json"), "rb") as f:
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
        with open(path.join(pathes.states, f"{self.name}.json"), "wb") as f:
            self.all[key] = value
            f.write(orjson.dumps(self.all, option=orjson.OPT_INDENT_2))

    def rename(self, new_name: str):
        if path.exists(path.join(pathes.states, f"{new_name}.json")):
            return False
        replace(
            path.join(pathes.states, f"{self.name}.json"),
            path.join(pathes.states, f"{new_name}.json"),
        )
        self.name = new_name
        self._info()


class states:
    def add(name, author):
        if path.exists(path.join(pathes.states, f"{name}.json")):
            return None
        with open(path.join(pathes.states, f"{name}.json"), "wb") as f:
            f.write(
                orjson.dumps(
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
                    option=orjson.OPT_INDENT_2,
                ),
            )
            return True

    def check(name):
        if path.exists(path.join(pathes.states, f"{name}.json")):
            return True
        return False

    def get_all(sortedby="players"):
        """Выдаёт все государства, сортированные по sortedby

        Аргумент:
            sortedby (str, optional): Автоматическая сортировка. По умолчанию "players",
            может быть "money"
        Возвращает:
            dict: Все государства сортированные в реверсе
        """
        all = {}
        for file in listdir(pathes.states):
            with open(path.join(pathes.states, file), "rb") as f:
                try:
                    all[file.replace(".json", "")] = orjson.loads(f.read())
                except JSONDecodeError:
                    logger.error(f"Не удалось просмотреть гос-во {file}")
        if sortedby == "money":

            def sort_key(item):
                return item[1][sortedby]
        else:  # По умолчанию сортируем по количеству игроков

            def sort_key(item):
                return len(item[1]["players"])

        return dict(sorted(all.items(), key=sort_key, reverse=True))

    def if_author(id: int):
        for file in listdir(pathes.states):
            with open(path.join(pathes.states, file), "rb") as f:
                if orjson.loads(f.read())["author"] == id:
                    return file.replace(".json", "")
        return False

    def if_player(id: int):
        for file in listdir(pathes.states):
            with open(path.join(pathes.states, file), "rb") as f:
                for player in orjson.loads(f.read())["players"]:
                    if player == id:
                        return file.replace(".json", "")
        return False

    def find(name: str) -> bool:
        if path.exists(path.join(pathes.states, f"{name}.json")):
            return True
        return False

    def remove(name: str) -> bool:
        state = path.join(pathes.states, f"{name}.json")
        if path.exists(state):
            pic = path.join(pathes.states_pic, f"{name}.png")
            if path.exists(pic):
                replace(pic, path.join(pathes.old_states, f"{name}.png"))
            replace(state, path.join(pathes.old_states, f"{name}.json"))
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
        self.pool = await asyncmy.create_pool(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.db,
            minsize=self.minsize,
            maxsize=self.maxsize,
        )

    async def get_by_id(self, id: int) -> dict[str, int]:
        async with self.pool.acquire() as conn, conn.cursor() as cur:
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
                return {
                    "wins_casino": result[0],
                    "lose_moneys_in_casino": result[1],
                }
            return {"wins_casino": 0, "lose_moneys_in_casino": 0}

    async def get_all(self) -> dict[int, dict[str, int]]:
        async with self.pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT id, wins_casino, lose_moneys_in_casino 
                FROM {self.table_name}
                """,
            )
            results = await cur.fetchall()
            return {
                row[0]: {
                    "wins_casino": row[1],
                    "lose_moneys_in_casino": row[2],
                }
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
    table_name=config.tokens.mysql_users.table,
)


class Notes:
    def __init__(self, storage_dir=pathes.notes):
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
        with open(file_path, encoding="utf8") as f:
            return f.read()

    def create(self, name: str, text: str):
        """Создать новую заметку. Возвращает True при успехе, False если уже существует."""
        file_path = self._get_file_path(name.lower())
        if path.exists(file_path):
            return False
        with open(file_path, "w", encoding="utf8") as f:
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


def check_withdraw_limit(id: int, amount: int) -> int | bool:
    if amount > 64:
        return 64
    today = datetime.now().date()
    if not path.exists(pathes.wdraw):
        logger.error("Файл вывода не найден!")
        data = {}
    else:
        with open(pathes.wdraw, "rb") as f:
            try:
                data = orjson.loads(f.read())
            except orjson.JSONDecodeError:
                logger.error("Ошибка при чтении файла вывода!")
                data = {}
    if str(id) in data:
        record_date = datetime.strptime(
            data[str(id)]["date"],
            "%Y-%m-%d",
        ).date()
        if record_date == today:
            already_withdrawn = data[str(id)]["withdrawn"]
            remaining = 64 - already_withdrawn
            if amount > remaining:
                return remaining
            data[str(id)] = {
                "date": today.isoformat(),
                "withdrawn": already_withdrawn + amount,
            }
        else:
            # Дата устарела, сбрасываем счетчик
            data[str(id)] = {"date": today.isoformat(), "withdrawn": amount}
    else:
        data[str(id)] = {"date": today.isoformat(), "withdrawn": amount}

    with open(pathes.wdraw, "wb") as f:
        f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
    return True


class RefCodes:
    def _read(self) -> dict:
        with open(pathes.ref, "rb") as f:
            return orjson.loads(f.read())

    def _write(self, data):
        with open(pathes.ref, "wb") as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))

    def get_own(self, id: int, default=None) -> str:
        return self._read().get(str(id), {}).get("own", default)

    def check_used(self, id: int, default=False) -> str:
        return self._read().get(str(id), {}).get("used", default)

    def add_own(self, id: int, name: str):
        if self.check_ref(name) is not None:
            return False
        load = self._read()
        if str(id) not in load:
            load[str(id)] = {}
        load[str(id)]["own"] = name
        self._write(load)

    def add_used(self, id: int, name: str):
        load = self._read()
        if str(id) not in load:
            load[str(id)] = {}
        load[str(id)]["used"] = name
        self._write(load)

    def check_ref(self, name) -> str:
        load = self._read()
        for id, data in load.items():
            try:
                if data.get("own").lower() == name.lower():
                    return id
            except Exception:
                pass


class CitiesGame:
    def __init__(self):
        self.data_file = pathes.cities
        self.data = self._load_data()

    def _load_data(self) -> dict:
        """Загружает данные из JSON файла или создаёт новый, если файла нет"""
        if path.exists(self.data_file):
            with open(self.data_file, "rb") as f:
                return orjson.loads(f.read())
        return {
            "current_game": {
                "players": [],
                "current_player_id": 0,
                "last_city": None,
                "cities": [],
            },
            "statistics": {},
            "status": False,
        }

    def logger(self, msg: str):
        logger.info(f"[Города] {msg}")

    def _save_data(self):
        """Сохраняет данные в JSON файл с помощью orjson"""
        with open(self.data_file, "wb") as f:
            f.write(orjson.dumps(self.data, option=orjson.OPT_INDENT_2))

    def get_players(self) -> list[int]:
        """Возвращает список ID игроков в текущем раунде"""
        return self.data["current_game"]["players"]

    def add_player(self, player_id: int):
        """Добавляет игрока в текущий раунд"""
        if player_id not in self.data["current_game"]["players"]:
            self.data["current_game"]["players"].append(player_id)
            self.data["start_players"] = self.data["start_players"] + 1
            self._save_data()

    def rem_player(self, player_id: int):
        """Удаляет игрока из текущего раунда
        Если игрок остался один, то игра завершается
        """
        self.next_answer()
        self.data["current_game"]["players"].remove(player_id)
        if len(self.data["current_game"]["players"]) < 2:
            return False
        self._save_data()
        return self.who_answer()

    def who_answer(self) -> int | None:
        """Возвращает ID игрока, который должен отвечать сейчас"""
        players = self.get_players()
        if not players:
            return None
        current_id = self.data["current_game"]["current_player_id"]
        return current_id

    def next_answer(self):
        """Переключает очередь на следующего игрока"""
        players = self.get_players()
        if not players:
            return False
        index = self.data["current_game"]["players"].index(
            self.data["current_game"]["current_player_id"],
        )
        try:
            self.data["current_game"]["current_player_id"] = self.data[
                "current_game"
            ]["players"][index + 1]
        except IndexError:
            self.data["current_game"]["current_player_id"] = self.data[
                "current_game"
            ]["players"][0]
        self.logger(
            f"Очередь игрока {self.data['current_game']['current_player_id']} отвечать",
        )
        self._save_data()

    def get_all_stat(self) -> dict[int, int]:
        """Возвращает отсортированную статистику по убыванию побед"""
        return dict(
            sorted(
                self.data["statistics"].items(),
                key=lambda item: item[1],
                reverse=True,
            ),
        )

    def end_game(self):
        """Завершает игру, очищая текущие данные"""
        self.data["current_game"] = {
            "players": [],
            "current_player_id": 0,
            "last_city": None,
            "cities": [],
        }
        self.data["start_players"] = 0
        self.data["status"] = False
        self.data["statistics"] = {}
        self.data["id"] = self.data["id"] + 1 if self.data["id"] < 10 else 1
        self.logger("Экземпляр Города закончен.")
        self._save_data()

    def start_game(self):
        """Начинает новую игру, сохраняя начальные данные"""
        city = choice(open(pathes.chk_city, encoding="utf8").read().split("\n"))
        self.data["id"] = self.data["id"] + 1 if self.data["id"] < 10 else 1
        self.data["status"] = True
        self.data["current_game"]["last_city"] = city
        self.logger(f"Запущена игра Города. Начинается с города {city}")
        self.data["current_game"]["current_player_id"] = choice(
            self.get_players(),
        )
        self.logger(f"Игроки: {self.get_players()}")
        self.logger(
            f"Отвечает: {self.data['current_game']['current_player_id']}",
        )
        self._save_data()
        return self.data

    def answer(self, id: str, city: str):
        city = city.strip().lower()
        if id not in self.data["current_game"]["players"]:
            self.logger(f"{id} не в списке игроков")
            return 3
        if id != self.data["current_game"]["current_player_id"]:
            self.logger(f"{id} сейчас не должен отвечать")
            return 2
        if city not in open(pathes.chk_city, encoding="utf8").read().split(
            "\n",
        ):
            self.logger(f"{id} ответил неизвестным городом")
            return 1
        if city[0] != formatter.city_last_letter(
            self.data["current_game"]["last_city"],
        ):
            self.logger(
                f"{id} ответил городом с разными буквами ({city[0]} != {self.data['current_game']['last_city'][-1]})",
            )
            return 4
        if city in self.data["current_game"]["cities"]:
            self.logger(f"{id} ответил городом, который был")
            return 5
        self.data["current_game"]["last_city"] = city
        self.data["statistics"][str(id)] = (
            self.data["statistics"].get(str(id), 0) + 1
        )
        self.data["current_game"]["cities"].append(city)
        self.next_answer()
        self._save_data()
        return 0

    def get_last_city(self) -> str | None:
        """Возвращает последний названный город"""
        return self.data["current_game"]["last_city"]

    def get_game_status(self):
        return self.data["status"]

    def get_count_players(self):
        return self.data["start_players"]

    def get_id(self):
        return self.data["id"]


def hellomsg_check(input_id):
    """Проверка, приветствовался ли человек ранее."""
    id_str = str(input_id)
    ids_set = list()
    if path.exists(pathes.hellomsg):
        try:
            with open(pathes.hellomsg, "rb") as f:
                ids_set = list(orjson.loads(f.read()))
        except (JSONDecodeError, FileNotFoundError):
            pass
    if id_str in ids_set:
        return False
    ids_set.append(id_str)
    with open(pathes.hellomsg, "wb") as f:
        f.write(orjson.dumps(ids_set, option=orjson.OPT_INDENT_2))
    return True


def mailing_get():
    try:
        with open(pathes.mailing, "rb") as f:
            return orjson.loads(f.read())
    except (FileNotFoundError, orjson.JSONDecodeError):
        return {"subscribers": []}


def mailing_save(data):
    """Сохранение данных в JSON файл"""
    with open(pathes.mailing, "wb") as f:
        f.write(orjson.dumps(data))
