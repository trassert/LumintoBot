async def database(key, value=None, delete=None, log=True):
    """Изменить/получить ключ из настроек"""
    if log:
        if value is not None:
            logger.info(f"Значение {key} теперь {value}")
        elif delete is not None:
            logger.info(f"Удаляю ключ: {key}")
        else:
            logger.info(f"Получаю ключ: {key}")

    data = await _load_json_async(pathes.data)

    if value is not None:
        data[key] = value
        data = dict(sorted(data.items()))
        await _save_json_async(pathes.data, data, indent=True)
        return True

    if delete is not None:
        data.pop(key, None)
        await _save_json_async(pathes.data, data, indent=True)
        return True

    return data.get(key)
