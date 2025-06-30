"NOIP синхронизация"

# try:
#     async with session.get(
#         f"http://{config.tokens.noip.name}:{config.tokens.noip.password}"
#         "@dynupdate.no-ip.com/"
#         f'nic/update?hostname={database("noip_host")}&myip={ipv4},{ipv6}',
#         headers={
#             "User-Agent": "Trassert MinecraftServer' \
#                 '/Windows 11-22000 s3pple@yandex.ru"
#         },
#     ) as response:
#         logger.info(await response.text())
#         message += "Связь с NOIP выполнена.\n"
# except Exception:
#     logger.error("Не удалось связаться с NOIP")
#     message += "Не удалось связаться с NOIP\n"
