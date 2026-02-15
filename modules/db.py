from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from random import choice, randint
from time import time
from typing import TypedDict

import aiofiles
import asyncmy
import orjson
from loguru import logger

from . import config, formatter, get_theme, pathes

logger.info(f"Загружен модуль {__name__}!")


def _load_json_sync(filepath: Path) -> dict:
    """Загружает JSON файл синхронно. Возвращает {} при ошибке."""
    try:
        with open(filepath, "rb") as f:
            raw = f.read()
        return orjson.loads(raw) if raw else {}
    except (FileNotFoundError, orjson.JSONDecodeError, ValueError):
        logger.error(f"Ошибка при чтении файла {filepath}")
        return {}


def _save_json_sync(
    filepath: Path, data: dict, sort_keys: bool = False, indent: bool = False
):
    """Сохраняет JSON файл синхронно."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    options = 0
    if sort_keys:
        options |= orjson.OPT_SORT_KEYS
    if indent:
        options |= orjson.OPT_INDENT_2
    with open(filepath, "wb") as f:
        f.write(orjson.dumps(data, option=options))


async def _load_json_async(filepath: Path) -> dict:
    """Загружает JSON файл асинхронно. Возвращает {} при ошибке."""
    try:
        async with aiofiles.open(filepath, "rb") as f:
            raw = await f.read()
        return orjson.loads(raw) if raw else {}
    except (FileNotFoundError, orjson.JSONDecodeError, ValueError):
        logger.error(f"Ошибка при чтении файла {filepath}")
        return {}


async def _save_json_async(
    filepath: Path, data: dict, sort_keys: bool = False, indent: bool = False
):
    """Сохраняет JSON файл асинхронно."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    options = 0
    if sort_keys:
        options |= orjson.OPT_SORT_KEYS
    if indent:
        options |= orjson.OPT_INDENT_2
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(orjson.dumps(data, option=options))


async def database(key, value=None, delete=None, log=True):
    """Изменить/получить ключ из настроек"""
    if log:
        if value is not None:
            logger.info(f"Значение {key} теперь {value}")
        elif delete is not None:
            logger.info(f"Удаляю ключ: {key}")
        else:
            logger.info(f"Получаю ключ: {key}")

    data = await _load_json_async(pathes.data)

    if value is not None:
        data[key] = value
        data = dict(sorted(data.items()))
        await _save_json_async(pathes.data, data, indent=True)
        return True

    if delete is not None:
        data.pop(key, None)
        await _save_json_async(pathes.data, data, indent=True)
        return True

    return data.get(key)


async def get_money(id) -> int:
    id = str(id)
    data = await _load_json_async(pathes.money)
    return data.get(id, 0)


async def get_all_money():
    """Получить все деньги"""
    data = await _load_json_async(pathes.money)
    return sum(data.values())


async def add_money(id, count):
    id = str(id)
    data = await _load_json_async(pathes.money)
    old = data.get(id, 0)
    data[id] = max(old + count, 0)
    await _save_json_async(pathes.money, data, indent=True)
    logger.info(f"Изменён баланс {id} ({old} -> {data[id]})")
    return data[id]


async def update_shop():
    """Обновляет магазин, возвращая новую тему."""
    last_theme_data = _load_json_sync(pathes.shopc)
    last_theme = last_theme_data.get("theme")
    all_themes = _load_json_sync(pathes.shop)

    if not all_themes:
        logger.exception("Файл shop_all.json пуст или не содержит тем.")
        return None

    theme_names = list(all_themes.keys())
    if not theme_names:
        logger.exception("Нет доступных тем в shop_all.json")
        return None

    new_theme = last_theme
    weights = await database("shop_weight")
    while new_theme == last_theme:
        new_theme = get_theme.weighted_choice(theme_names, weights)

    theme_items = all_themes[new_theme]
    item_names = list(theme_items.keys())
    if len(item_names) < 5:
        logger.exception(
            f"В теме '{new_theme}' недостаточно предметов (минимум 5, найдено {len(item_names)})"
        )
        return None

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
        elif not isinstance(price, (int, float)):
            logger.exception(f"Некорректный формат цены для предмета '{item}': {price}")
        current_shop[item] = item_data

    _save_json_sync(pathes.shopc, current_shop, indent=True)
    return new_theme


async def get_shop() -> dict:
    return await _load_json_async(pathes.shopc)


async def ready_to_mine(id: str) -> bool:
    id = str(id)
    data = await _load_json_async(pathes.mine)
    now = int(time())
    last = data.get(id, 0)
    if now - last > config.cfg.MineWait:
        data[id] = now
        await _save_json_async(pathes.mine, data, indent=True)
        return True
    return False


class Roles:
    BLACKLIST = -1
    USER = 0
    VIP = 1
    INTERN = 2
    MODER = 3
    ADMIN = 4
    OWNER = 5

    async def get(self, id: str) -> int:
        """Получить роль пользователя (USER, если не найдено)"""
        id = str(id)
        data = await _load_json_async(pathes.roles)
        return data.get(id, self.USER)

    async def set(self, id: str, role: int) -> bool:
        """Установить роль пользователя"""
        id = str(id)
        role = int(role)
        data = await _load_json_async(pathes.roles)
        data[id] = role
        sorted_data = dict(sorted(data.items(), key=lambda x: (-x[1], x[0])))
        await _save_json_async(pathes.roles, sorted_data, indent=True)
        return True


class Crorostat:
    def __init__(self, id=False):
        if id:
            self.id = str(id)

    def get(self):
        data = _load_json_sync(pathes.crocostat)
        if self.id in data:
            return data[self.id]
        data[self.id] = 0
        _save_json_sync(pathes.crocostat, data, sort_keys=True)
        return 0

    async def add(self):
        data = await _load_json_sync(pathes.crocostat)
        data[self.id] = data.get(self.id, 0) + 1
        await _save_json_sync(pathes.crocostat, data, sort_keys=True)

    async def get_all(self=False):
        data = await _load_json_sync(pathes.crocostat)
        return dict(sorted(data.items(), key=lambda item: item[1], reverse=True))


class nicks:
    def __init__(self, nick=None, id=None):
        self.nick = nick
        self.id = id

    def get(self, if_nothing=None) -> str:
        if self.nick:
            data = _load_json_sync(pathes.nick)
            nick_lower = self.nick.lower()
            for key, value in data.items():
                if key.lower() == nick_lower:
                    return value
            return if_nothing
        if self.id:
            data = _load_json_sync(pathes.nick)
            for key, value in data.items():
                if value == self.id:
                    return key
            return if_nothing
        return if_nothing

    def get_all(self):
        data = _load_json_sync(pathes.nick)
        return dict(sorted(data.items()))

    def link(self):
        data = _load_json_sync(pathes.nick)
        keys_to_remove = [k for k, v in data.items() if v == self.id]
        for k in keys_to_remove:
            del data[k]
        data[self.nick] = int(self.id)
        _save_json_sync(pathes.nick, data, indent=True)
        return True


class statistic:
    def __init__(self, days=1):
        self.days = days

    def get(self, nick, all_days=False, data=False):
        filepath = pathes.stats / f"{nick}.json"
        if not filepath.exists():
            stats = {datetime.now().strftime("%Y.%m.%d"): 0}
            _save_json_sync(filepath, stats, sort_keys=True)
            return 0

        stats = _load_json_sync(filepath)
        if all_days:
            return sum(stats.values()) or 0

        start_date = datetime.now() - timedelta(days=self.days)
        filtered = {
            date: value
            for date, value in stats.items()
            if datetime.strptime(date, "%Y.%m.%d") >= start_date
        }
        return filtered if data else sum(filtered.values()) or 0

    def get_all(self, all_days=False):
        data = {}
        for file in pathes.stats.iterdir():
            if file.suffix != ".json":
                continue
            nick = file.stem
            nick_stat = self.get(nick, all_days=all_days)
            if nick_stat > 1:
                data[nick] = nick_stat
        return sorted(data.items(), key=lambda item: item[1], reverse=True)

    def add(self, date=None):
        now = date or datetime.now().strftime("%Y.%m.%d")
        filepath = pathes.stats / f"{self}.json"
        stats = _load_json_sync(filepath)
        stats[now] = stats.get(now, 0) + 1
        _save_json_sync(filepath, stats, sort_keys=True)

    def get_raw(self) -> dict[str, int]:
        totals = defaultdict(int)
        for json_file in pathes.stats.iterdir():
            if json_file.suffix != ".json":
                continue
            filepath = json_file
            try:
                data = _load_json_sync(filepath)
                for date, count in data.items():
                    totals[date] += count
            except Exception:
                logger.error(f"Ошибка при чтении файла - {json_file.name}")
                continue

        if self.days <= 0:
            return dict(sorted(totals.items(), key=lambda item: item[0]))

        start_date = datetime.now() - timedelta(days=self.days)
        return {
            date: value
            for date, value in totals.items()
            if datetime.strptime(date, "%Y.%m.%d") >= start_date
        }


class ticket:
    def get(self):
        self = str(self)
        if not pathes.tickets.exists():
            _save_json_sync(pathes.tickets, {})
            return None
        data = _load_json_sync(pathes.tickets)
        return data.get(self)

    def add(self, value):
        data = _load_json_sync(pathes.tickets)
        while True:
            random_id = str(randint(1000, 9999))
            if random_id not in data:
                break
        data[random_id] = {"author": int(self), "value": int(value)}
        _save_json_sync(pathes.tickets, data, indent=True)
        return random_id

    def delete(self):
        data = _load_json_sync(pathes.tickets)
        if self not in data:
            return None
        del data[self]
        _save_json_sync(pathes.tickets, data, indent=True)
        return True


class state:
    def __init__(self, name):
        self.name = name
        self._info()

    def _info(self):
        data = _load_json_sync(pathes.states / f"{self.name}.json")
        self.all = data
        self.price = data["price"]
        self.enter = data["enter"]
        self.desc = data["desc"]
        self.players = data["players"]
        self.type = data["type"]
        self.date = data["date"]
        self.author = data["author"]
        self.coordinates = data["coordinates"]
        self.money = data["money"]

    def change(self, key, value):
        self.all[key] = value
        _save_json_sync(pathes.states / f"{self.name}.json", self.all, indent=True)

    def rename(self, new_name: str):
        new_path = pathes.states / f"{new_name}.json"
        if new_path.exists():
            return False
        (pathes.states / f"{self.name}.json").rename(new_path)
        self.name = new_name
        self._info()
        return None


class states:
    def add(self, author):
        filepath = pathes.states / f"{self}.json"
        if filepath.exists():
            return None
        data = {
            "price": 0,
            "enter": True,
            "desc": "Пусто",
            "players": [],
            "type": 0,
            "date": datetime.now().strftime("%Y.%m.%d"),
            "money": 0,
            "author": author,
            "coordinates": "Не найдено",
        }
        _save_json_sync(filepath, data, indent=True)
        return True

    def check(self):
        return (pathes.states / f"{self}.json").exists()

    def get_all(self="players"):
        all_data = {}
        for file in pathes.states.iterdir():
            if file.suffix != ".json":
                continue
            name = file.stem
            try:
                all_data[name] = _load_json_sync(file)
            except Exception:
                logger.error(f"Не удалось просмотреть гос-во {file.name}")
        if self == "money":

            def key_func(item):
                return item[1]["money"]
        else:

            def key_func(item):
                return len(item[1]["players"])

        return dict(sorted(all_data.items(), key=key_func, reverse=True))

    def if_author(self: int):
        for file in pathes.states.iterdir():
            if file.suffix != ".json":
                continue
            data = _load_json_sync(file)
            if data["author"] == self:
                return file.stem
        return False

    def if_player(self: int):
        for file in pathes.states.iterdir():
            if file.suffix != ".json":
                continue
            data = _load_json_sync(file)
            if self in data["players"]:
                return file.stem
        return False

    def find(self: str) -> bool:
        return (pathes.states / f"{self}.json").exists()

    def remove(self: str) -> bool:
        state_path = pathes.states / f"{self}.json"
        if not state_path.exists():
            return False
        pic_path = pathes.states_pic / f"{self}.png"
        if pic_path.exists():
            pic_path.rename(pathes.old_states / f"{self}.png")
        state_path.rename(pathes.old_states / f"{self}.json")
        return True


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
                f"SELECT wins_casino, lose_moneys_in_casino FROM {self.table_name} WHERE id = %s",
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
                f"SELECT id, wins_casino, lose_moneys_in_casino FROM {self.table_name}"
            )
            results = await cur.fetchall()
            return {
                row[0]: {"wins_casino": row[1], "lose_moneys_in_casino": row[2]}
                for row in results
            }

    async def add_win(self, id: int):
        async with self.pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                f"INSERT INTO {self.table_name} (id, wins_casino, lose_moneys_in_casino) "
                f"VALUES (%s, 1, 0) ON DUPLICATE KEY UPDATE wins_casino = wins_casino + 1",
                (id,),
            )
            await conn.commit()

    async def add_lose_money(self, id: int, amount: int = 1):
        async with self.pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                f"INSERT INTO {self.table_name} (id, wins_casino, lose_moneys_in_casino) "
                f"VALUES (%s, 0, %s) ON DUPLICATE KEY UPDATE lose_moneys_in_casino = lose_moneys_in_casino + %s",
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
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, name):
        return self.storage_dir / f"{name}.txt"

    def get(self, name: str):
        file_path = self._get_file_path(name.lower())
        if not file_path.exists():
            return None
        with open(file_path, encoding="utf8") as f:
            return f.read()

    def create(self, name: str, text: str):
        file_path = self._get_file_path(name.lower())
        if file_path.exists():
            return False
        with open(file_path, "w", encoding="utf8") as f:
            f.write(text)
        return True

    def remove(self, name: str):
        file_path = self._get_file_path(name.lower())
        if not file_path.exists():
            return False
        file_path.unlink()
        return True

    def get_all(self) -> list[str]:
        if not self.storage_dir.exists():
            return []
        return [f.stem for f in self.storage_dir.iterdir() if f.is_file()]


def check_withdraw_limit(id: int, amount: int) -> int | bool:
    if amount > 64:
        return 64
    today = datetime.now().date()
    data = _load_json_sync(pathes.wdraw)

    id_str = str(id)
    if id_str in data:
        record_date = datetime.strptime(data[id_str]["date"], "%Y-%m-%d").date()
        if record_date == today:
            already_withdrawn = data[id_str]["withdrawn"]
            remaining = 64 - already_withdrawn
            if amount > remaining:
                return remaining
            data[id_str]["withdrawn"] = already_withdrawn + amount
        else:
            data[id_str] = {"date": today.isoformat(), "withdrawn": amount}
    else:
        data[id_str] = {"date": today.isoformat(), "withdrawn": amount}

    _save_json_sync(pathes.wdraw, data, indent=True)
    return True


class RefCodes:
    async def _read(self) -> dict:
        return await _load_json_async(pathes.ref)

    async def _write(self, data):
        return await _save_json_async(pathes.ref, data, indent=True)

    async def get_own(self, id: int, default=None) -> str:
        return (await self._read()).get(str(id), {}).get("own", default)

    async def check_uses(self, id: int, default=None) -> list[str]:
        if default is None:
            default = []
        return (await self._read()).get(str(id), {}).get("used", default)

    async def add_own(self, id: int, name: str):
        if await self.check_ref(name) is not None:
            return False
        load = await self._read()
        if str(id) not in load:
            load[str(id)] = {}
        load[str(id)]["own"] = name
        await self._write(load)
        return None

    async def add_uses(self, id: int, who_used: int):
        load = await self._read()
        used_list = load.get(str(id), {}).get("used", [])
        used_list.append(str(who_used))
        load[str(id)]["used"] = used_list
        await self._write(load)

    async def check_ref(self, name) -> str:
        load = await self._read()
        for user_id, data in load.items():
            try:
                if data.get("own", "").lower() == name.lower():
                    return user_id
            except Exception:
                pass
        return None

    async def delete(self, id) -> bool:
        "Удаляет реф. код, return bool True/False (есть рефка или нет)"
        load = await self._read()
        try:
            del load[str(id)]["own"]
        except KeyError:
            return False
        await self._write(load)
        return True

    async def get_top_uses(self) -> list[list[str, int]]:
        result = []
        for user_id, info in (await self._read()).items():
            used = info.get("used", None)
            if used:
                result.append([user_id, len(used)])
        return sorted(result, key=lambda x: x[1], reverse=True)


class CitiesGame:
    def __init__(self):
        self.data_file = pathes.cities
        self.data = self._load_data()

    def _load_data(self) -> dict:
        if self.data_file.exists():
            return _load_json_sync(self.data_file)
        return {
            "current_game": {
                "players": [],
                "current_player_id": 0,
                "last_city": None,
                "cities": [],
            },
            "statistics": {},
            "status": False,
            "start_players": 0,
            "id": 0,
        }

    def logger(self, msg: str):
        logger.info(f"[Города] {msg}")

    def _save_data(self):
        _save_json_sync(self.data_file, self.data, indent=True)

    def get_players(self) -> list[int]:
        return self.data["current_game"]["players"]

    def add_player(self, player_id: int):
        if player_id not in self.data["current_game"]["players"]:
            self.data["current_game"]["players"].append(player_id)
            self.data["start_players"] = self.data.get("start_players", 0) + 1
            self._save_data()

    def rem_player(self, player_id: int):
        self.next_answer()
        if player_id in self.data["current_game"]["players"]:
            self.data["current_game"]["players"].remove(player_id)
        if len(self.data["current_game"]["players"]) < 2:
            return False
        self._save_data()
        return self.who_answer()

    def who_answer(self) -> int | None:
        players = self.get_players()
        return self.data["current_game"]["current_player_id"] if players else None

    def next_answer(self):
        players = self.get_players()
        if not players:
            return
        current_id = self.data["current_game"]["current_player_id"]
        if current_id not in players:
            self.data["current_game"]["current_player_id"] = players[0]
            self._save_data()
            return
        idx = players.index(current_id)
        self.data["current_game"]["current_player_id"] = players[
            (idx + 1) % len(players)
        ]
        self.logger(
            f"Очередь игрока {self.data['current_game']['current_player_id']} отвечать"
        )
        self._save_data()

    def get_all_stat(self) -> dict[int, int]:
        return dict(
            sorted(
                self.data["statistics"].items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

    def end_game(self):
        self.data["current_game"] = {
            "players": [],
            "current_player_id": 0,
            "last_city": None,
            "cities": [],
        }
        self.data["start_players"] = 0
        self.data["status"] = False
        self.data["statistics"] = {}
        self.data["id"] = (self.data.get("id", 0) + 1) % 10 or 1
        self.logger("Экземпляр Города закончен.")
        self._save_data()

    def start_game(self):
        city = choice((pathes.chk_city).read_text(encoding="utf8").splitlines())
        self.data["id"] = (self.data.get("id", 0) + 1) % 10 or 1
        self.data["status"] = True
        self.data["current_game"]["last_city"] = city
        self.data["current_game"]["current_player_id"] = choice(self.get_players())
        self.logger(f"Запущена игра Города. Начинается с города {city}")
        self.logger(f"Игроки: {self.get_players()}")
        self.logger(f"Отвечает: {self.data['current_game']['current_player_id']}")
        self._save_data()
        return self.data

    def answer(self, id: str, city: str):
        city = city.strip().lower()
        players = self.data["current_game"]["players"]
        if str(id) not in map(str, players):
            self.logger(f"{id} не в списке игроков")
            return 3
        if str(id) != str(self.data["current_game"]["current_player_id"]):
            self.logger(f"{id} сейчас не должен отвечать")
            return 2
        valid_cities = set((pathes.chk_city).read_text(encoding="utf8").splitlines())
        if city not in valid_cities:
            self.logger(f"{id} ответил неизвестным городом")
            return 1
        last_city = self.data["current_game"]["last_city"]
        if city[0] != formatter.city_last_letter(last_city):
            self.logger(
                f"{id} ответил городом с разными буквами ({city[0]} != {last_city[-1]})"
            )
            return 4
        if city in self.data["current_game"]["cities"]:
            self.logger(f"{id} ответил городом, который был")
            return 5
        self.data["current_game"]["last_city"] = city
        self.data["statistics"][str(id)] = self.data["statistics"].get(str(id), 0) + 1
        self.data["current_game"]["cities"].append(city)
        self.next_answer()
        self._save_data()
        return 0

    def get_last_city(self) -> str | None:
        return self.data["current_game"]["last_city"]

    def get_game_status(self):
        return self.data["status"]

    def get_count_players(self):
        return self.data.get("start_players", 0)

    def get_id(self):
        return self.data.get("id", 0)


def hellomsg_check(input_id):
    id_str = str(input_id)
    ids_list = _load_json_sync(pathes.hellomsg)
    if not isinstance(ids_list, list):
        ids_list = []
    if id_str in ids_list:
        return False
    ids_list.append(id_str)
    _save_json_sync(pathes.hellomsg, ids_list, indent=True)
    return True


def mailing_get():
    data = _load_json_sync(pathes.mailing)
    return data if isinstance(data, dict) else {"subscribers": []}


def mailing_save(data):
    _save_json_sync(pathes.mailing, data)


async def get_votes(player: str) -> int:
    player = str(player)
    data = await _load_json_async(pathes.votes)
    return data.get(player, 0)


async def add_votes(player: str, count: int = 1) -> None:
    player = str(player)
    data = await _load_json_async(pathes.votes)
    data[player] = data.get(player, 0) + count
    if data[player] == config.cfg.Advancements.Votes:
        pass
    await _save_json_async(pathes.votes, data)


async def get_crocodile_word() -> str:
    words = await _load_json_async(pathes.crocomap)
    return choice(list(words))


async def add_pending_hint(user_id: int | str, hint_string: str, word: str) -> int:
    data = await _load_json_async(pathes.pending_hints)
    pending_id = max((int(k) for k in data), default=0) + 1
    data[str(pending_id)] = {
        "user": str(user_id),
        "hint": str(hint_string),
        "word": str(word),
    }
    await _save_json_async(pathes.pending_hints, data, indent=True)
    return pending_id


async def remove_pending_hint(id: int | str):
    data = await _load_json_async(pathes.pending_hints)
    if str(id) not in data:
        return None
    del data[str(id)]
    await _save_json_async(pathes.pending_hints, data, indent=True)
    return True


async def get_latest_pending_hint() -> dict:
    data = await _load_json_async(pathes.pending_hints)
    try:
        hint_id = list(data.keys())[-1]
    except IndexError:
        return {}
    hint = data.get(hint_id, {})
    hint["id"] = hint_id
    return hint


async def get_hint_byid(id: str | int) -> dict | None:
    data = await _load_json_async(pathes.pending_hints)
    return data.get(str(id))


async def append_hint(word: str, hint: str):
    data = await _load_json_async(pathes.crocomap)
    word_hints = data.get(word, [])
    if hint not in word_hints:
        word_hints.append(hint)
    data[word] = word_hints
    await _save_json_async(pathes.crocomap, data, indent=True)


async def add_mine_top(id: int | str, count: int):
    id = str(id)
    data = await _load_json_async(pathes.mine_stat)
    data[id] = data.get(id, 0) + int(count)
    await _save_json_async(pathes.mine_stat, data, indent=True)


async def get_mine_top() -> list[list[str, int]]:
    return sorted(
        (await _load_json_async(pathes.mine_stat)).items(), key=lambda x: -x[1]
    )


class Item(TypedDict):
    author_id: int
    item: str
    count: int
    price: int


async def add_item(id: str, author_id: int, item: str, count: int, price: int) -> None:
    """Добавляет новый товар по ID. Перезаписывает, если уже существует."""
    data = await _load_json_async(pathes.items)
    data[str(id)] = {
        "author_id": author_id,
        "item": item,
        "count": count,
        "price": price,
    }
    await _save_json_async(pathes.items, data, indent=True)


async def get_item(id: str) -> Item | None:
    """Возвращает товар по ID или None, если не найден."""
    data = await _load_json_async(pathes.items)
    raw_item = data.get(str(id))
    if raw_item is None:
        return None
    return raw_item


async def remove_item(id: str) -> bool:
    """Удаляет товар по ID. Возвращает True, если существовал и удалён."""
    data = await _load_json_async(pathes.items)
    id = str(id)
    if id not in data:
        return False
    del data[id]
    await _save_json_async(pathes.items, data, indent=True)
    return True
