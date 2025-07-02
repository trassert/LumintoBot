# [KeyboardButtonCallback(text="💎 Внести изумруды", data=b"casino.start")],

# if data[1] == "start":
#             balance = db.get_money(event.sender_id)
#             if balance < config.coofs.PriceForCasino:
#                 return await event.answer(
#                     phrase.money.not_enough.format(decline_number(balance, "изумруд")),
#                     alert=True,
#                 )
#             db.add_money(event.sender_id, -config.coofs.PriceForCasino)
#             await event.answer(phrase.casino.do)
#             response = []

#             async def check(message):
#                 if event.sender_id != message.sender_id:
#                     return
#                 if getattr(message, "media", None) is None:
#                     return
#                 if getattr(message.media, "emoticon", None) is None:
#                     return
#                 if message.media.emoticon != "🎰":
#                     return
#                 pos = dice.get(message.media.value)
#                 if (pos[0] == pos[1]) and (pos[1] == pos[2]):
#                     logger.info(f"{message.sender_id} - победил в казино")
#                     db.add_money(
#                         message.sender_id,
#                         config.coofs.PriceForCasino * config.coofs.CasinoWinRatio,
#                     )
#                     await asyncio.sleep(2)
#                     await message.reply(
#                         phrase.casino.win.format(
#                             config.coofs.PriceForCasino * config.coofs.CasinoWinRatio
#                         )
#                     )
#                 elif (pos[0] == pos[1]) or (pos[1] == pos[2]):
#                     db.add_money(message.sender_id, config.coofs.PriceForCasino)
#                     await asyncio.sleep(2)
#                     await message.reply(phrase.casino.partially)
#                 else:
#                     logger.info(f"{message.sender_id} проиграл в казино")
#                     await asyncio.sleep(2)
#                     await message.reply(phrase.casino.lose)
#                 client.remove_event_handler(check)
#                 logger.info("Снят обработчик казино")
#                 response.append(1)

#             client.add_event_handler(check, events.NewMessage(config.chats.chat))
#             await asyncio.sleep(config.coofs.CasinoSleepTime)
#             if 1 not in response:
#                 return await event.answer(
#                     phrase.casino.timeout.format(await get_name(event.sender_id))
#                 )