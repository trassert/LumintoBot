"Пинг ИИ"

# for server in ai.ai_servers:
#     timestamp = time()
#     async with session.get(f"https://{server}/") as request:
#         try:
#             if await request.text() == "ok":
#                 server_ping = round(time() - timestamp, 1)
#                 textping = (
#                     f"{server_ping} сек."
#                     if server_ping > 0
#                     else phrase.ping.min_ai
#                 )
#                 all_servers_ping.append(f"🌐 : ИИ сервер №{n} - {textping}")
#             else:
#                 all_servers_ping.append(f"❌ : ИИ сервер №{n} - Ошибка!")
#         except Exception:
#             all_servers_ping.append(f"❌ : ИИ сервер №{n} - Выключен!")
#     n += 1