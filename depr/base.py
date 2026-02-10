# @func.new_command(r"/слово (.+)")
# async def word_request(event: Message):
#     word = event.pattern_match.group(1).strip().lower()
#     with open(pathes.crocoall, encoding="utf-8") as f:
#         if word in f.read().split("\n"):
#             return await event.reply(phrase.word.exists)
#     with open(pathes.crocobl, encoding="utf-8") as f:
#         if word in f.read().split("\n"):
#             return await event.reply(phrase.word.in_blacklist)
#     entity = await func.get_name(event.sender_id)
#     logger.info(f'Пользователь {event.sender_id} хочет добавить слово "{word}"')
#     keyboard = types.ReplyInlineMarkup(
#         [
#             types.KeyboardButtonRow(
#                 [
#                     types.KeyboardButtonCallback(
#                         "✅ Добавить",
#                         f"word.yes.{word}.{event.sender_id}".encode(),
#                     ),
#                     types.KeyboardButtonCallback(
#                         "❌ Отклонить",
#                         f"word.no.{word}.{event.sender_id}".encode(),
#                     ),
#                 ]
#             ),
#         ]
#     )
#     try:
#         await client.send_message(
#             config.tokens.bot.creator,
#             phrase.word.request.format(
#                 user=entity,
#                 word=word,
#                 hint=await ai.CrocodileChat.send_message(word),
#             ),
#             buttons=keyboard,
#         )
#     except tgerrors.ButtonDataInvalidError:
#         return await event.reply(phrase.word.long)
#     return await event.reply(phrase.word.set.format(word=word))


# @func.new_command(r"/слова\s([\s\S]+)")
# async def word_requests(event: Message):
#     words = [
#         w.strip()
#         for w in event.pattern_match.group(1).strip().lower().split()
#         if w.strip()
#     ]
#     if not words:
#         return await event.reply(phrase.word.empty_long)
#     text = ""
#     message = await event.reply(phrase.word.checker)

#     def load_wordlist(filepath):
#         with open(filepath, encoding="utf-8") as f:
#             return set(f.read().split("\n"))

#     existing = load_wordlist(pathes.crocoall)
#     blacklisted = load_wordlist(pathes.crocobl)
#     pending = []
#     for word in words:
#         if word in existing:
#             text += f"Слово **{word}** - есть\n"
#         elif word in blacklisted:
#             text += f"Слово **{word}** - в ЧС\n"
#         else:
#             pending.append(word)
#         await message.edit(text)
#         await asyncio.sleep(0.5)
#     if not pending:
#         return
#     entity = await func.get_name(event.sender_id)
#     for word in pending:
#         logger.info(
#             f'Пользователь {event.sender_id} хочет добавить слово "{word}"'
#         )
#         keyboard = types.ReplyInlineMarkup(
#             [
#                 types.KeyboardButtonRow(
#                     [
#                         types.KeyboardButtonCallback(
#                             "✅ Добавить",
#                             f"word.yes.{word}.{event.sender_id}".encode(),
#                         ),
#                         types.KeyboardButtonCallback(
#                             "❌ Отклонить",
#                             f"word.no.{word}.{event.sender_id}".encode(),
#                         ),
#                     ]
#                 ),
#             ]
#         )
#         try:
#             await client.send_message(
#                 config.tokens.bot.creator,
#                 phrase.word.request.format(
#                     user=entity,
#                     word=word,
#                     hint=await ai.CrocodileChat.send_message(word),
#                 ),
#                 buttons=keyboard,
#             )
#             text += f"Слово **{word}** - проверяется\n"
#         except tgerrors.ButtonDataInvalidError:
#             text += f"Слово **{word}** - слишком длинное\n"
#         await message.edit(text)
#         await asyncio.sleep(0.5)


# @func.new_command(r"/слова$")
# async def word_requests_empty(event: Message):
#     return await event.reply(phrase.word.empty_long)


# @func.new_command(r"/слово$")
# async def word_request_empty(event: Message):
#     return await event.reply(phrase.word.empty)


# @func.new_command(r"\-слово$")
# async def word_remove_empty(event: Message):
#     roles = db.roles()
#     if roles.get(event.sender_id) < roles.ADMIN:
#         return await event.reply(
#             phrase.roles.no_perms.format(
#                 level=roles.ADMIN, name=phrase.roles.admin
#             )
#         )
#     return await event.reply(phrase.word.rem_empty)


# @func.new_command(r"\-слово\s(.+)")
# async def word_remove(event: Message):
#     roles = db.roles()
#     if roles.get(event.sender_id) < roles.ADMIN:
#         return await event.reply(
#             phrase.roles.no_perms.format(
#                 level=roles.ADMIN, name=phrase.roles.admin
#             )
#         )
#     word = event.pattern_match.group(1).strip().lower()
#     with open(pathes.crocoall, encoding="utf-8") as f:
#         wordlist = f.read().split("\n")
#     if word not in wordlist:
#         return await event.reply(phrase.word.not_exists)
#     wordlist.remove(word)
#     with open(pathes.crocoall, "w", encoding="utf-8") as f:
#         f.write("\n".join(wordlist))
#     return await event.reply(phrase.word.deleted.format(word))
