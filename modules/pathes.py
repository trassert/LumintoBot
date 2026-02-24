from pathlib import Path

from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

# Конфиг
config = Path("configs")

# Директории и файлы в db/crocodile/
crocoall = Path("db") / "crocodile" / "all.txt"
crocobl = Path("db") / "crocodile" / "blacklist.txt"
crocomap = Path("db") / "crocodile" / "mappings.json"
crocodile = Path("db") / "crocodile" / "game.json"
pending_hints = Path("db") / "crocodile" / "pending_hints.json"

# Директория timings
mine = Path("db") / "timings" / "mine.json"

# Директория users
roles = Path("db") / "users" / "roles.json"
money = Path("db") / "users" / "money.json"
nick = Path("db") / "users" / "nicks.json"
wdraw = Path("db") / "users" / "withdraws.json"
ref = Path("db") / "users" / "ref.json"
crocostat = Path("db") / "users" / "crocodile_stat.json"
hellomsg = Path("db") / "users" / "hellomsg.json"
votes = Path("db") / "users" / "votes.json"
mine_stat = Path("db") / "users" / "mine.json"

# Корневые файлы в db/
items = Path("db") / "items.json"
tickets = Path("db") / "tickets.json"
mailing = Path("db") / "mailing.json"
tasks = Path("db") / "tasks.json"
data = Path("db") / "data.json"
shopc = Path("db") / "shop_current.json"
shop = Path("db") / "shop_all.json"

# Директория cities
cities = Path("db") / "cities" / "game.json"
chk_city = Path("db") / "cities" / "cities.txt"
bl_city = Path("db") / "cities" / "blacklist.txt"

# Директории
bot = Path("db") / "bot"
states = Path("db") / "states"
times = Path("db") / "time"
notes = Path("db") / "notes"
stats = Path("db") / "chat_stats"
shop_log = Path("log") / "shop"

old_states = Path("backup") / "states"

font = Path("fonts") / "minecraft.ttf"

chart = Path("charts") / "chart.png"

states_pic = Path("images") / "states"

pic = Path("images")
