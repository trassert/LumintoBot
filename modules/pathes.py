from os import path

from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

crocoall = path.join("db", "crocodile", "all.txt")
crocobl = path.join("db", "crocodile", "blacklist.txt")
crocomap = path.join("db", "crocodile", "mappings.json")

pending_hints = path.join("db", "crocodile", "pending_hints.json")

mine = path.join("db", "timings", "mine.json")

roles = path.join("db", "users", "roles.json")
money = path.join("db", "users", "money.json")
nick = path.join("db", "users", "nicks.json")
wdraw = path.join("db", "users", "withdraws.json")
ref = path.join("db", "users", "ref.json")
crocostat = path.join("db", "users", "crocodile_stat.json")
hellomsg = path.join("db", "users", "hellomsg.json")
votes = path.join("db", "users", "votes.json")

tickets = path.join("db", "tickets.json")
mailing = path.join("db", "mailing.json")
tasks = path.join("db", "tasks.json")
embeddings = path.join("db", "embeddings.json")
data = path.join("db", "data.json")
shopc = path.join("db", "shop_current.json")
shop = path.join("db", "shop_all.json")

cities = path.join("db", "cities", "game.json")
chk_city = path.join("db", "cities", "cities.txt")
bl_city = path.join("db", "cities", "blacklist.txt")

bot = path.join("db", "bot")
states = path.join("db", "states")
times = path.join("db", "time")
notes = path.join("db", "notes")
stats = path.join("db", "chat_stats")
shop_log = path.join("log", "shop")

old_states = path.join("backup", "states")

font = path.join("fonts", "minecraft.ttf")

chart = path.join("charts", "chart.png")

states_pic = path.join("images", "states")

pic = "images"