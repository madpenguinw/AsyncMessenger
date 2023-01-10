import asyncio

from aioconsole import ainput

from constants import CHAT, DISCONNECT, EXIT, HOST, MAXBYTES, PORT


class Client:
    def __init__(self, server_host: str = HOST, server_port: int = PORT):
        self.server_host = server_host
        self.server_port = server_port
        self.disconnect: bool = False

    async def start_client(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.server_host, self.server_port)
        await asyncio.gather(self.write_msg(), self.read_msg())

    async def write_msg(self):
        while True:
            message = await ainput('')
            if message == DISCONNECT:
                print('<Отключение от сервера...>')
                self.disconnect = True
                self.writer.close()
                break
            self.writer.write(message.encode())
            await self.writer.drain()
            await asyncio.sleep(0.1)  # Needed for task changing

    async def read_msg(self):
        while True:
            if self.disconnect:
                break
            if msg_to_read := await self.reader.read(MAXBYTES):
                decoded_msg = msg_to_read.decode()
                if decoded_msg.startswith(CHAT):
                    # for clients synchronization in private chats
                    command = '/silent_chat ' + decoded_msg
                    self.writer.write(command.encode())
                    await self.writer.drain()
                    print(decoded_msg)
                elif decoded_msg.startswith(EXIT):
                    self.writer.write(EXIT.encode())
                    await self.writer.drain()
                else:
                    print(decoded_msg)
        self.writer.close()


if __name__ == '__main__':
    client = Client()
    asyncio.run(client.start_client())
