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

# @client.on(events.NewMessage(pattern=r'(?i)^/чара(.*)'))
# @client.on(events.NewMessage(pattern=r'(?i)^/чарка(.*)'))
# @client.on(events.NewMessage(pattern=r'(?i)^/зачарование(.*)'))
# @client.on(events.NewMessage(pattern=r'(?i)^/enchant(.*)'))
# @client.on(events.NewMessage(pattern=r'(?i)^что за чара(.*)'))
# @client.on(events.NewMessage(pattern=r'(?i)^чарка(.*)'))
# @client.on(events.NewMessage(pattern=r'(?i)^зачарование(.*)'))
# async def get_enchant(event):
#     arg = event.pattern_match.group(1)
#     if arg.strip() == '':
#         return await event.reply(phrase.enchant.no_arg)
#     desc = get_enchant_desc(arg)
#     if desc is None:
#         return await event.reply(phrase.enchant.no_diff)
#     return await event.reply(phrase.enchant.main.format(desc))





# # async def stat(event):
#     entity = await client.get_entity(event.sender_id)
#     if event.text.startswith('‹'):
#         if event.sender_id in settings('api_bot_id', log=False):
#             id = give_id_by_nick_minecraft(
#                 event.text.split(
#                     '›'
#                 )[0].split(
#                     '‹'
#                 )[1]
#             )
#             if id is not None:
#                 add_stat(id)
#     try:
#         if not entity.bot:
#             add_stat(event.sender_id)
#     except AttributeError:
#         pass


# async def push_unactive(event):
#     participants = await client.get_participants(
#         tokens.bot.chat
#     )
#     list_ids = [user.id for user in participants]
#     list_db = []
#     for filename in listdir(path.join('db', 'user_stats')):
#         if filename.endswith('.json'):
#             list_db.append(int(filename.replace('.json', '')))
#     list_names = []
#     for id in list_ids:
#         if id not in list_db:
#             user = await client.get_entity(id)
#             if not user.bot:
#                 if user.username:
#                     list_names.append(
#                         f'@{user.username}'
#                     )
#                 else:
#                     list_names.append(
#                         f'[{user.first_name}](tg://user?id={id})'
#                     )
#     return await event.reply(
#         phrase.unactive+' '.join(list_names)
#     )


# async def stat_check(event):
#     try:
#         days = int(
#             event.text.replace(
#                 '/моя стата', ''
#             ).replace(
#                 '/mystat', ''
#             ).replace(
#                 '/мстат', ''
#             ).replace(
#                 'сколько я написал', ''
#             )
#         )
#     except ValueError:
#         days = 1
#     return await event.reply(
#         phrase.stat.format(
#             messages=give_stat(event.sender_id, days),
#             time=days
#         )
#     )


# async def active_check(event):
#     try:
#         days = int(
#             event.text.replace(
#                 '/актив', ''
#             ).replace(
#                 '/топ актив', ''
#             ).replace(
#                 '/топ соо', ''
#             ).replace(
#                 '/top active', ''
#             )
#         )
#     except ValueError:
#         days = 1
#     text = phrase.active.format(days)
#     n = 1
#     for data in get_active(days):
#         try:
#             if data[1] != 1:
#                 entity = await client.get_entity(int(data[0]))
#                 name = entity.first_name
#                 if entity.last_name is not None:
#                     name += f' {entity.last_name}'
#                 text += f'{n}. {name}: {data[1]}\n'
#                 n += 1
#         except ValueError as e:
#             logger.error(e)
#             remove(path.join('db', 'user_stats', f'{data[0]}.json'))
#     return await event.reply(text)


# muted = '''**🤫 : Пользователю {user} запрещено писать**
# 🤔 : Причина: {reason}
# ⏳ : На время: {time}
# '''
# mute_help = '''🤫 : Это команда мут!
# Вот как её использовать
# `/мут @человека минуты.часы.дни причина`
# `/мут @человека минуты.часы причина`
# `/мут @человека минуты причина`
# ❗️ : Причину вставлять не обязательно!
# '''
# mute_time_error = '❌ : Неверно определено время!'
# stat = '📊 : Вы написали {messages} сообщений за {time} дней'
# no_word_admin = '❌ : Слово не найдено! Или вы не админ!'
# active = '📊 : Топ **активных людей** за {} дней: \n'
# unactive = '📊 : Созыв всех неактивных!\n'
# is_admin = '❌ : Невозможно сделать это - пользователь обладает префиксом.'
# no_word = '❌ : Слово не найдено!'

# async def mute_user(event):
#     if event.sender_id not in settings('admins_id'):
#         return await event.reply(phrase.no_perm)
#     args = event.text.split(" ", maxsplit=3)[1:]
#     if args[0] in ['помощь', 'help']:
#         return await event.reply(phrase.mute_help)
#     user_link = args[0]
#     if len(args) > 2:
#         reason = ' '.join(args[2:])
#     else:
#         reason = 'Нет'
#     if '.' in args[1]:
#         stamp = args[1].split(".")
#         if len(stamp) == 3:
#             until_date = timedelta(
#                 minutes=int(stamp[0]),
#                 hours=int(stamp[1]),
#                 days=int(stamp[2])
#             )
#         elif len(stamp) == 2:
#             until_date = timedelta(
#                 minutes=int(stamp[0]),
#                 hours=int(stamp[1]),
#             )
#         else:
#             return await event.reply(phrase.mute_time_error)
#     else:
#         until_date = timedelta(minutes=int(args[1]))
#     user = await client.get_entity(user_link)
#     try:
#         await client.edit_permissions(
#             entity=event.chat_id,
#             user=user.id,
#             send_messages=False,
#             send_media=False,
#             send_stickers=False,
#             send_gifs=False,
#             send_games=False,
#             send_inline=False,
#             send_polls=False,
#             until_date=until_date
#         )
#         return await event.reply(
#             phrase.muted.format(
#                 user=user.first_name,
#                 time=str(until_date
#             ).replace(':00', '').replace('day', 'дней'),
#                 reason=reason
#             ),
#         )
#     except UserAdminInvalidError:
#         return await event.reply(phrase.is_admin)


'Сервер обновлений'

# def update_server(host):
#     app = Flask(__name__)

#     @app.route("/download")
#     def download():
#         logger.info("Отдаю файл")
#         q = request.args.get("q")
#         try:
#             client_version = int(request.args.get("version"))
#             logger.info(f'Версия клиента: {client_version}')
#         except:
#             return "versionerror"
#         if q not in ["prog", "mods"]:
#             return "typeerror"
#         logger.info(
#             'Клиенту нужно - {type}'.format(
#                 type='Программа' if q == 'prog' else 'Моды'
#                 )
#             )
#         file = path.join("update", q, str(client_version), "content.zip")
#         logger.info(file)
#         return send_file(file, None, True)

#     @app.route("/get_image")
#     def get_image():
#         image = choice(listdir("images"))
#         return send_file(path.join("images", image), download_name=image)

#     serve(app, host=host, port="5000")
# Thread(
#     target=update_server,
#     args=(settings("ipv6"),),
#     daemon=True
# ).start()
# Thread(
#     target=update_server,
#     args=("0.0.0.0",),
#     daemon=True
# ).start()

'Стата'

# def add_stat(id):
#     'Добавляет статистику'

#     now = datetime.now().strftime("%Y.%m.%d")
#     'Если для пользователя нет файла'
#     if not path.exists(path.join('db', 'user_stats', f'{id}.json')):
#         with open(
#             path.join('db', 'user_stats', f'{id}.json'),
#             'w',
#             encoding='utf8'
#         ) as f:
#             stats = {}
#             stats[now] = 1
#             return json.dump(
#                 stats, f, indent=4, ensure_ascii=False, sort_keys=True
#             )

#     'Если для пользователя есть файл'
#     with open(
#         path.join('db', 'user_stats', f'{id}.json'), 'r', encoding='utf8'
#     ) as f:
#         stats = json.load(f)
#         if now in stats:
#             stats[now] += 1
#         else:
#             stats[now] = 1
#     with open(
#         path.join('db', 'user_stats', f'{id}.json'), 'w', encoding='utf8'
#     ) as f:
#         return json.dump(
#             stats, f, indent=4, ensure_ascii=False, sort_keys=True
#         )


# def give_stat(id, days=1):
#     now = datetime.now().strftime("%Y.%m.%d")

#     'Если нет файла'
#     if not path.exists(path.join('db', 'user_stats', f'{id}.json')):
#         with open(
#             path.join('db', 'user_stats', f'{id}.json'),
#             'w',
#             encoding='utf8'
#         ) as f:
#             stats = {}
#             stats[now] = 1
#             json.dump(
#                 stats, f, indent=4, ensure_ascii=False, sort_keys=True
#             )
#             return 1

#     'Если есть файл'
#     with open(
#         path.join('db', 'user_stats', f'{id}.json'), 'r', encoding='utf8'
#     ) as f:
#         now = datetime.now()
#         stats = json.load(f)
#         dates = list(stats.keys())
#         dates.sort(reverse=True)
#         start_date = now - timedelta(days=days)
#         filtered_data = {
#             date: value for date, value in stats.items() if datetime.strptime(
#                 date, '%Y.%m.%d') >= start_date
#         }
#         return sum(filtered_data.values()) or 1


# def get_active(days=1, reverse=True):
#     'Получить актив пользователей'

#     data = {}
#     for file in listdir(path.join('db', 'user_stats')):
#         id = file.replace('.json', '')
#         data[id] = give_stat(id, days)
#     return sorted(data.items(), key=lambda item: item[1], reverse=reverse)

'ДБ варнов'

# def get_warns(id):
#     id = str(id)
#     with open(
#         path.join('db', 'warns.json'), 'r', encoding='utf8'
#     ) as f:
#         data = json.load(f)
#     if id in data:
#         return data[id]
#     else:
#         with open(
#             path.join('db', 'warns.json'), 'r', encoding='utf8'
#         ) as f:
#             data[id] = {}
#             json.dump(
#                 data, f, indent=4, ensure_ascii=False, sort_keys=True
#             )
#         return {}

'Варны'

# def set_warn(id):
#     id = str(id)
#     with open(
#         path.join('db', 'warns.json'), 'r', encoding='utf8'
#     ) as f:
#         data = json.load(f)
#     if id in data:
#         if len(data[id]) == data('max_warns')-1:
#             data[id] = {}
#             warns = data('max_warns')
#         else:
#             data[id][str(len(data[id])+1)] = time()
#             warns = len(data[id])
#     with open(
#         path.join('db', 'warns.json'), 'r', encoding='utf8'
#     ) as f:
#         json.dump(
#             data, f, indent=4, ensure_ascii=False, sort_keys=True
#         )
#     return warns

'Устаревшие хандлеры'

# 'Добавление статистики'
# client.add_event_handler(
#     stat, events.NewMessage(chats=tokens.bot.chat)
# )

# 'Пуш неактивных'
# client.add_event_handler(
#     push_unactive, events.NewMessage(incoming=True, pattern="/пуш неактив")
# )
# client.add_event_handler(
#     push_unactive, events.NewMessage(incoming=True, pattern="/unactive")
# )

# 'Мут'
# client.add_event_handler(
#     mute_user, events.NewMessage(incoming=True, pattern="/мут")
# )
# client.add_event_handler(
#     mute_user, events.NewMessage(incoming=True, pattern="/mute")
# )

# 'Мут'
# client.add_event_handler(
#     mute_user, events.NewMessage(incoming=True, pattern="/мут")
# )
# client.add_event_handler(
#     mute_user, events.NewMessage(incoming=True, pattern="/mute")
# )

# 'Моя стата'
# client.add_event_handler(
#     stat_check,
#     events.NewMessage(incoming=True, pattern="/моя стата")
# )
# client.add_event_handler(
#     stat_check,
#     events.NewMessage(incoming=True, pattern="/mystat")
# )
# client.add_event_handler(
#     stat_check,
#     events.NewMessage(incoming=True, pattern="/мстат")
# )
# client.add_event_handler(
#     stat_check,
#     events.NewMessage(incoming=True, pattern="сколько я написал")
# )

# 'Стата беседы'
# client.add_event_handler(
#     active_check, events.NewMessage(incoming=True, pattern="/актив")
# )
# client.add_event_handler(
#     active_check, events.NewMessage(incoming=True, pattern="/топ актив")
# )
# client.add_event_handler(
#     active_check, events.NewMessage(incoming=True, pattern="/топ соо")
# )
# client.add_event_handler(
#     active_check, events.NewMessage(incoming=True, pattern="/top active")
# )


'Помощь по модам'
# await event.reply(phrase.help.mods, link_preview=True)
# await asyncio.sleep(1)

# mods = '💻 : [Установка модов](https://teletype.in/@trassert/mods)'

"Версия лаунчера"

# async def version(request):
#         q = request.query.get('q')
#         try:
#             version = int(request.query.get("version"))
#         except (ValueError, TypeError):
#             return aiohttp.web.Response(
#                 text="versionerror"
#             )
#         if q not in ["prog", "mods"]:
#             return aiohttp.web.Response(
#                 text="typeerror"
#             )
#         current = max(list(map(int, listdir(path.join("update", q)))))
#         if version < current:
#             return aiohttp.web.Response(
#                 text=str(version + 1)
#             )
#         else:
#             return aiohttp.web.Response(
#                 text="True"
#             )

# def similar(word, list):
#     max_ratio = 0
#     max_simular = ""
#     for n in list:
#         diff = difflib.SequenceMatcher(a=word.lower(), b=n.lower()).ratio()
#         if diff > 0.6 and diff > max_ratio:
#             max_ratio = diff
#             max_simular = n
#     logger.info(
#         "Выполнен поиск слова\n"
#         f'Искомое: "{word}"\n'
#         f'Найдено: "{max_simular if max_simular != "" else "Ничего"}"'
#     )
#     return max_simular


# def get_enchant_desc(string):
#     with open(path.join("db", "enchants", "ru.json"), encoding="utf-8") as f:
#         ru = json.load(f)
#     with open(path.join("db", "enchants", "en.json"), encoding="utf-8") as f:
#         en = json.load(f)
#     data = {**ru, **en}
#     enchant = similar(string, list(data.keys()))
#     if enchant != "":
#         return data[enchant]
#     return None
