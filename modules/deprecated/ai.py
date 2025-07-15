"Стрим, работает некорректно"

# async def get_stream(id: int, message: str):
#     async for chunk in await chat.send_message_stream(f"{id} написал: {message}"):
#         logger.warning(chunk)
#         if chunk.text:
#             yield chunk.text

"Обработчик ИИ"

# async def gemini(event: Message):
#     arg = event.pattern_match.group(1).strip()
#     response = await ai.response(arg)
#     if response is None:
#         return await event.reply(phrase.server.overload)
#     if len(response) > 4096:
#         for x in range(0, len(response), 4096):
#             await event.reply(response[x : x + 4096])
#     else:
#         return await event.reply(response)

# async def response(message):
#     "Запрос к Google Gemini"
#     async with aiohttp.ClientSession() as session:
#         for server in ai_servers:
#             (
#                 logger.info(f"Выполняю запрос к AI: {message}")
#                 if len(message) < 100
#                 else logger.info(f"Выполняю запрос к AI: {message[:100]}...")
#             )
#             try:
#                 async with session.get(
#                     url=f"https://{server}/gemini?q={message}&token={config.tokens.google}"
#                 ) as request:
#                     if request.status == codes.ok:
#                         return formatter.rm_badtext(await request.text())
#             except Exception:
#                 pass
#     return None


# ai_servers = ["trassert0reserve.pythonanywhere.com", "trassert.pythonanywhere.com"]
