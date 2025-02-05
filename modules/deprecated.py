client = ''
settings = ''
give_id_by_nick_minecraft = ''
add_stat = ''
UserAdminInvalidError = ''
tokens = ''
listdir = ''
path = ''
phrase = ''
give_stat = ''
get_active = ''
logger = ''
remove = ''
timedelta = ''


async def stat(event):
    entity = await client.get_entity(event.sender_id)
    if event.text.startswith('‹'):
        if event.sender_id in settings('api_bot_id', log=False):
            id = give_id_by_nick_minecraft(
                event.text.split(
                    '›'
                )[0].split(
                    '‹'
                )[1]
            )
            if id is not None:
                add_stat(id)
    try:
        if not entity.bot:
            add_stat(event.sender_id)
    except AttributeError:
        pass


async def push_unactive(event):
    participants = await client.get_participants(
        tokens.bot.chat
    )
    list_ids = [user.id for user in participants]
    list_db = []
    for filename in listdir(path.join('db', 'user_stats')):
        if filename.endswith('.json'):
            list_db.append(int(filename.replace('.json', '')))
    list_names = []
    for id in list_ids:
        if id not in list_db:
            user = await client.get_entity(id)
            if not user.bot:
                if user.username:
                    list_names.append(
                        f'@{user.username}'
                    )
                else:
                    list_names.append(
                        f'[{user.first_name}](tg://user?id={id})'
                    )
    return await event.reply(
        phrase.unactive+' '.join(list_names)
    )


async def stat_check(event):
    try:
        days = int(
            event.text.replace(
                '/моя стата', ''
            ).replace(
                '/mystat', ''
            ).replace(
                '/мстат', ''
            ).replace(
                'сколько я написал', ''
            )
        )
    except ValueError:
        days = 1
    return await event.reply(
        phrase.stat.format(
            messages=give_stat(event.sender_id, days),
            time=days
        )
    )


async def active_check(event):
    try:
        days = int(
            event.text.replace(
                '/актив', ''
            ).replace(
                '/топ актив', ''
            ).replace(
                '/топ соо', ''
            ).replace(
                '/top active', ''
            )
        )
    except ValueError:
        days = 1
    text = phrase.active.format(days)
    n = 1
    for data in get_active(days):
        try:
            if data[1] != 1:
                entity = await client.get_entity(int(data[0]))
                name = entity.first_name
                if entity.last_name is not None:
                    name += f' {entity.last_name}'
                text += f'{n}. {name}: {data[1]}\n'
                n += 1
        except ValueError as e:
            logger.error(e)
            remove(path.join('db', 'user_stats', f'{data[0]}.json'))
    return await event.reply(text)


async def mute_user(event):
    if event.sender_id not in settings('admins_id'):
        return await event.reply(phrase.no_perm)
    args = event.text.split(" ", maxsplit=3)[1:]
    if args[0] in ['помощь', 'help']:
        return await event.reply(phrase.mute_help)
    user_link = args[0]
    if len(args) > 2:
        reason = ' '.join(args[2:])
    else:
        reason = 'Нет'
    if '.' in args[1]:
        stamp = args[1].split(".")
        if len(stamp) == 3:
            until_date = timedelta(
                minutes=int(stamp[0]),
                hours=int(stamp[1]),
                days=int(stamp[2])
            )
        elif len(stamp) == 2:
            until_date = timedelta(
                minutes=int(stamp[0]),
                hours=int(stamp[1]),
            )
        else:
            return await event.reply(phrase.mute_time_error)
    else:
        until_date = timedelta(minutes=int(args[1]))
    user = await client.get_entity(user_link)
    try:
        await client.edit_permissions(
            entity=event.chat_id,
            user=user.id,
            send_messages=False,
            send_media=False,
            send_stickers=False,
            send_gifs=False,
            send_games=False,
            send_inline=False,
            send_polls=False,
            until_date=until_date
        )
        return await event.reply(
            phrase.muted.format(
                user=user.first_name,
                time=str(until_date
            ).replace(':00', '').replace('day', 'дней'),
                reason=reason
            ),
        )
    except UserAdminInvalidError:
        return await event.reply(phrase.is_admin)


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
