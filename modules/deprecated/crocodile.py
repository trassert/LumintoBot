"Старые подсказки крокодила."

# last_hint = db.database("crocodile_last_hint")
# and last_hint != 0

# if last_hint != 0:
#     check_last = "Так же учитывай, " f"что подсказка {last_hint} уже была."
# else:
#     check_last = ""
# response = await ai.response(
#     f'Сделай подсказку для слова "{word}". '
#     'Ни в коем случае не добавляй никаких "подсказка для слова.." '
#     "и т.п, ответ должен содержать только подсказку. "
#     "Не забудь, что подсказка не должна "
#     "содержать слово в любом случае. " + check_last
# )
# if response is None:
#     game = db.database("current_game")
#     hint = game["hints"]
#     hint.remove(event.sender_id)
#     game["hints"] = hint
#     db.database("current_game", game)
#     return await event.reply(phrase.crocodile.error)
# db.database("crocodile_last_hint", response)