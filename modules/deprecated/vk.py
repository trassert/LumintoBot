# @client.on.chat_message()
# async def tg_chat(message: Message):
#     try:
#         user_info = await client.api.users.get(user_ids=message.from_id)
#         name = "{} {}".format(user_info[0].first_name, user_info[0].last_name)
#     except IndexError:
#         return logger.info("Юзер не найден, пропускаем")
#     logger.info(f"ВК>ТГ: {name} > {message.text}")
#     return await telegram.client.send_message(
#         config.chats.chat,
#         reply_to=config.chats.topics.vk,
#         message=f"**{name}**\n{message.text}",
#     )
# client = Bot(token=config.tokens.vk.token)
# class CaseRule(ABCRule[Message]):
#     def __init__(self, command: str):
#         self.command = command.lower()

#     async def check(self, message: Message) -> bool:
#         return message.text.lower() == self.command


# @client.on.message(CaseRule("/ip"))
# @client.on.message(CaseRule("/айпи"))
# @client.on.message(CaseRule("/хост"))
# @client.on.message(CaseRule("/host"))
# async def host(message: Message):
#     logger.info("Запрошен IP в ВК")
#     await message.reply(phrase.server.host.format(db.database("host")))


# @client.on.message(regex=r"(?i)^/пинг(.*)")
# async def ping(message: Message, match: tuple):
#     text = await crosssocial.ping(
#         message.date,
#         match[0].strip(),
#         vk=True
#     )
#     if text is None: return
#     return await message.reply(text)


"Обработчик вк-топика"


# @client.on(events.NewMessage(config.chats.chat))
# async def vk_chat(event: Message):

#     async def send():
#         if event.text == "":
#             return logger.info("Пустое сообщение")
#         user_name = await client.get_entity(event.sender_id)
#         if user_name.last_name is None:
#             user_name = user_name.first_name
#         else:
#             user_name = user_name.first_name + " " + user_name.last_name
#         logger.info(f"ТГ>ВК: {user_name} > {event.text}")
#         await vk.client.api.messages.send(
#             chat_id=config.tokens.vk.chat_id,
#             message=f"{user_name}: {event.text}",
#             random_id=0,
#         )

#     if (
#         event.reply_to_msg_id == config.chats.topics.vk
#     ) or (
#         getattr(event.reply_to, "reply_to_top_id") == config.chats.topics.vk
#     ):
#         return await send()

