import asyncio

from aioconsole import ainput

from constants import HOST, PORT, DISCONNECT


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
        msg_to_write: str = ''
        while msg_to_write != DISCONNECT:
            message = await ainput('<Enter your message:> \n')  # Delete on prod
            if message == DISCONNECT:
                print('<Disconnecting...>')
                self.disconnect = True
                self.writer.close()
                break
            self.writer.write(message.encode())
            await self.writer.drain()
            print('<Message sent>')
            await asyncio.sleep(0.1)  # Needed for task changing

    async def read_msg(self):
        msg_to_read: str = ''
        while True:
            if self.disconnect:
                break
            print('<Reading message...>')  # Delete on prod
            msg_to_read = await self.reader.read(1024)
            if msg_to_read:
                print(f'<Received: {msg_to_read.decode()}>')
        self.writer.close()


if __name__ == '__main__':
    client = Client()
    asyncio.run(client.start_client())
