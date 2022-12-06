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
        self.port: int = port
        self.clients_dict: dict[str, tuple[StreamReader, StreamWriter]] = {}

    async def connecting_clients(
            self, reader: StreamReader, writer: StreamWriter) -> None:
        # if add 'self.' -> get last_client, not current
        current_address: tuple = writer.get_extra_info('peername')
        current_client_host: str = current_address[0]
        current_client_port: int = current_address[1]
        current_client: str = current_client_host + str(current_client_port)
        if current_client not in self.clients_dict.keys():
            self.clients_dict[current_client] = (reader, writer)
        logger.info('Client connected at %(host)s:%(port)s',
                    {'host': current_client_host, 'port': current_client_port})

        while True:
            data: bytes = await reader.read(1024)
            if not data:
                break  # User disconnection
            msg: str = data.decode()
            if msg.startswith(PRIVATE):
                await self.private_msg(msg, current_client)
            else:
                await self.public_msg(msg, current_client)

        logger.info('Client disconnected at %(host)s:%(port)s',
                    {'host': current_client_host, 'port': current_client_port})
        writer.close()

    async def start(self) -> None:
        srv = await asyncio.start_server(
            self.connecting_clients, self.host, self.port)
        logger.info('Server started at %(host)s:%(port)s',
                    {'host': self.host, 'port': self.port})

        async with srv:
            await srv.serve_forever()

    async def public_msg(self, msg: str, current_client: str) -> None:
        for client in self.clients_dict.keys():
            if client != current_client:
                msg_to_send = current_client + ': ' + msg
                writer: StreamWriter = self.clients_dict[client][1]
                writer.write(msg_to_send.encode())
                await writer.drain()

    async def private_msg(self, msg: str, current_client: str) -> None:
        pass


if __name__ == '__main__':
    server = Server()
    asyncio.run(server.start())
