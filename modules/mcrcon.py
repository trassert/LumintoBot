import asyncio
import struct

# Определяем исключения для обработки ошибок клиента
class ClientError(Exception):
    """Базовое исключение для ошибок клиента."""
    pass

class InvalidPassword(ClientError):
    """Исключение для неверного пароля."""
    pass

class MinecraftClient:
    """
    Асинхронный клиент для подключения к RCON серверу Minecraft.
    """
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password

        self._auth = None
        self._reader = None
        self._writer = None

    async def __aenter__(self):
        """
        Метод-контекстный менеджер для входа.
        Инициализирует соединение, если оно еще не установлено, и выполняет аутентификацию.
        """
        if not self._writer:
            try:
                self._reader, self._writer = await asyncio.open_connection(
                    self.host, self.port
                )
                await self._authenticate()
            except ConnectionRefusedError:
                raise ClientError("Не удалось подключиться к серверу. Проверьте хост и порт.")

        return self

    async def __aexit__(self, exc_type, exc, tb):
        """
        Метод-контекстный менеджер для выхода.
        Закрывает соединение с сервером.
        """
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()  # ! Ждать закрытия

    async def _authenticate(self):
        """Выполняет аутентификацию на сервере RCON."""
        if not self._auth:
            await self._send(3, self.password)
            self._auth = True

    async def _read_data(self, leng):
        """
        Считывает указанное количество байт из потока.
        """
        data = b""
        while len(data) < leng:
            packet = await self._reader.read(leng - len(data))
            if not packet:
                break
            data += packet
        return data

    async def _send(self, typen, message):
        """
        Отправляет команду на сервер и получает все пакеты ответа,
        объединяя их в одну строку.
        """
        if not self._writer:
            raise ClientError("Не подключён.")

        # Отправляем пакет с командой
        out = struct.pack("<li", 0, typen) + message.encode("utf8") + b"\x00\x00"
        out_len = struct.pack("<i", len(out))
        self._writer.write(out_len + out)
        await self._writer.drain()

        # Читаем все пакеты ответа с очень коротким тайм-аутом
        responses = []
        while True:
            try:
                # Читаем длину пакета с коротким тайм-аутом
                in_len_bytes = await asyncio.wait_for(self._reader.read(4), timeout=0.1)
                if not in_len_bytes:
                    break
                in_len = struct.unpack("<i", in_len_bytes)[0]
                
                # Читаем полезную нагрузку
                in_payload = await self._read_data(in_len)
            except asyncio.TimeoutError:
                # Если срабатывает тайм-аут, значит, сервер прекратил отправку данных.
                # Это означает, что ответ завершен.
                break
            except (asyncio.IncompleteReadError, struct.error):
                raise ClientError("Соединение разорвано или данные некорректны.")

            in_id, in_type = struct.unpack("<ii", in_payload[:8])
            in_data, in_padd = in_payload[8:-2], in_payload[-2:]

            if in_padd != b"\x00\x00":
                raise ClientError("Неправильное заполнение.")
            if in_id == -1:
                raise InvalidPassword("Неверный пароль.")
            if in_type == 2:  # RconPacketType.SERVERDATA_EXECCOMMAND
                # Это часть многострочного ответа, добавляем её.
                responses.append(in_data.decode("utf8"))
            elif in_type == 0:  # RconPacketType.SERVERDATA_RESPONSE_VALUE (терминатор)
                # Этот пакет сигнализирует об окончании ответа, выходим из цикла.
                break
            else:
                raise ClientError(f"Получен пакет с неправильным типом: {in_type}.")

        # Объединяем все части ответа в одну строку с переносами.
        return "\n".join(responses)

    async def send(self, cmd):
        """
        Отправляет команду на сервер и возвращает результат.
        """
        result = await self._send(2, cmd)
        return result
