# async def genai(request: aiohttp.web.Request):
#     player = request.query.get("player")
#     text = request.query.get("text")
#     logger.info(f"[AI] {player} > {text}")
#     chat = await ai.get_player_chat(player)
#     return aiohttp.web.Response(text=(await chat.send_message(text)).text)
# aiohttp.web.get("/genai", genai),
