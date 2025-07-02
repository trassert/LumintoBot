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