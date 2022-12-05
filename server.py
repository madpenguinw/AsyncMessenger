import logging
import asyncio
from asyncio.streams import StreamReader, StreamWriter

import app_logger
from constants import HOST, PORT, PRIVATE

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Server:
    def __init__(self, host: str = HOST, port: int = PORT):
        self.host: str = host
        self.port: str = port
        self.clients_dict: dict[str, tuple[StreamReader, StreamWriter]] = {}

    async def connecting_clients(
            self, reader: StreamReader, writer: StreamWriter) -> None:
        address: tuple = writer.get_extra_info('peername')
        client_host: str = address[0]
        client_port: int = address[1]
        client: str = client_host + str(client_port)
        if client not in self.clients_dict.keys():
            self.clients_dict[client] = (reader, writer)
        logger.info('Client connected at %(host)s:%(port)s',
                    {'host': client_host, 'port': client_port})

        while True:
            data: bytes = await reader.read(1024)
            if not data:
                break  # User disconnection
            msg: str = data.decode()
            if msg.startswith(PRIVATE):
                self.private_msg(msg)
            else:
                await self.public_msg(msg)

        logger.info('Client disconnected at %(host)s:%(port)s',
                    {'host': client_host, 'port': client_port})
        writer.close()

    async def start(self) -> None:
        srv = await asyncio.start_server(
            self.connecting_clients, self.host, self.port)
        logger.info('Server started at %(host)s:%(port)s',
                    {'host': self.host, 'port': self.port})

        async with srv:
            await srv.serve_forever()

    async def public_msg(self, msg_to_send: str) -> None:
        for client in self.clients_dict.keys():
            writer: StreamWriter = self.clients_dict[client][1]
            writer.write(msg_to_send.encode())
            await writer.drain()

    def private_msg(self, msg_to_send: str) -> None:
        pass


if __name__ == '__main__':
    server = Server()
    asyncio.run(server.start())
