import asyncio
import logging
from asyncio.streams import StreamReader, StreamWriter
from collections import deque

import app_logger
from constants import (ADD_TO_CHAT, ADDED_TO_CHAT, ADMIN_OFFLINE,
                       ALREADY_IN_CHAT, AUTHORIZATION, AUTHORIZATION_FAILED,
                       CHAT, CHAT_CONNECTED, CHAT_CREATED, CHAT_EXIST,
                       CHAT_NOT_EXIST, CHATS, CREATE, EMPTY_HISTORY, EXIT,
                       GREETING, HISTORY, HOST, JOIN, JOIN_REFUSED, LOGIN,
                       MAXLENGTH, ME, NOT_IN_CHAT, NOT_REGISTERED, PASSWORD,
                       PASSWORED_CHANGED, PORT, PRIVATE, REGISTERED,
                       REGISTRATION, REGISTRATION_FAILED, RETRY, RULES,
                       SUCCESSFULLY_AUTHORIZED, SUCCESSFULLY_REGISTERED,
                       USERNAME, WRONG_COMMAND, YES)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# TODO проверить работу дисконнектов во время регистрации/авторизации
# TODO добавить подпись к каждому отправленному сообщению, из какого чата оно


class Server:
    def __init__(self, host: str = HOST, port: int = PORT):
        self.host: str = host
        self.port: int = port
        self.address_writer_reader: dict[
            str, tuple[StreamWriter, StreamReader]] = {}
        self.login_password: dict[str, str] = {}
        self.login_address: dict[str, list[str]] = {}
        self.chat_logins: dict[str, tuple[str, list[str]]] = {}
        self.login_chats: dict[str, list[str]] = {}
        self.short_history: deque = deque(maxlen=MAXLENGTH)

    async def create_chat(
            self, msg: str, login: str, writer: StreamWriter) -> None:
        """User can create chat and become its admin."""
        chat: str = msg.split(' ', maxsplit=1)[1]
        logger.info('Attempt %(login)s create chat %(chat)s',
                    {'login': login, 'chat': chat})  # DELETE
        print(-1)
        if chat in self.chat_logins.keys():
            print(0)
            await self.write_msg(CHAT_EXIST, writer=writer)
        else:
            # first el in tuple -> chat admin
            self.chat_logins[chat] = (login, [login])
            self.login_chats[login].append(chat)
            await self.write_msg(CHAT_CREATED, writer=writer)
            logger.info('User %(login)s created chat %(chat)s',
                        {'login': login, 'chat': chat})

    async def join_chat(
            self, msg: str, login: str, writer: StreamWriter) -> None:
        """Send to admin request for joining to chat."""
        # 1 если уже есть в чате
        chat: str = msg.split(' ', maxsplit=1)[1]
        if chat in self.chat_logins.keys():
            if login in self.chat_logins[chat][1]:
                await self.write_msg(ALREADY_IN_CHAT, writer=writer)
            else:
                admin = self.chat_logins[chat][0]
                if admin in self.login_address.keys():
                    if self.login_address[login]:
                        for address in self.login_address[login]:
                            # First answered admins client should
                            # break the awaiting
                            await self.write_msg(ADD_TO_CHAT, address=admin)
                            answer = await self.read_msg(address=address)
                            if answer == YES:
                                self.chat_logins.append(login)
                                self.login_chats[login].append(chat)
                                logger.info(
                                    'User %(login)s joined chat %(chat)s',
                                    {'login': login, 'chat': chat})
                                await self.write_msg(
                                    ADDED_TO_CHAT, writer=writer)
                                break
                            else:
                                await self.write_msg(
                                    JOIN_REFUSED, writer=writer)
                                break
                    else:
                        await self.write_msg(ADMIN_OFFLINE, writer=writer)
                else:
                    await self.write_msg(ADMIN_OFFLINE, writer=writer)
        else:
            await self.write_msg(CHAT_NOT_EXIST, writer=writer)

    async def chat_msg(self, msg: str, login: str) -> None:
        chat_msg: str = ''
        chat: str = msg.split(' ', maxsplit=1)[1]
        if chat in self.chat_logins.keys():
            if login in self.chat_logins[chat][1]:
                for address in self.login_address[login]:
                    await self.write_msg(CHAT_CONNECTED, address=address)
                    logger.info(
                        'User "%(login)s" connected to private chat '
                        '"%(chat)s"',
                        {'login': login, 'chat': chat})

                    while chat_msg != EXIT:
                        chat_msg = await self.read_msg(address=address)

                        if chat_msg == EXIT:
                            logger.info(
                                'User "%(login)s" disconnected from private '
                                'chat "%(chat)s"',
                                {'login': login, 'chat': chat})
                            break

                        msg_to_others = \
                            login + ': ' + chat_msg + ' | private chat' + chat
                        for user in self.chat_logins[chat][1]:
                            if user != login:
                                if self.login_address[user]:
                                    for client in self.login_address[user]:
                                        await self.write_msg(
                                            msg_to_others, address=client)

                        msg_to_myself = \
                            ME + ': ' + chat_msg + ' | private chat' + chat
                        for my_address in self.login_address[login]:
                            if my_address != address:
                                await self.write_msg(msg_to_myself)
                    break
            else:
                for address in self.login_address[login]:
                    await self.write_msg(NOT_IN_CHAT, address=address)
        else:
            for address in self.login_address[login]:
                await self.write_msg(CHAT_NOT_EXIST, address=address)

    async def show_chats(self, login: str):
        """Shows all chats the user is a member of"""
        for chat in self.login_chats[login]:
            for address in self.login_address[login]:
                await self.write_msg(chat, address=address)

    async def start(self) -> None:
        """Start the server."""
        srv = await asyncio.start_server(
            self.connecting_clients, self.host, self.port)
        logger.info('Server started at %(host)s:%(port)s',
                    {'host': self.host, 'port': self.port})

        async with srv:
            await srv.serve_forever()

    async def connecting_clients(
            self, reader: StreamReader, writer: StreamWriter) -> None:
        """Connect clients to the server."""

        # address -> 'HOST:PORT' of current client
        # if add 'self.' -> get address of last connected client, not current
        address = self.get_clients_address(writer)
        self.address_writer_reader[address] = (writer, reader)
        login: str = await self.greeting_client(writer, reader)
        self.login_chats[login] = []

        logger.info(
            'Client connected at %(address)s as %(login)s',
            {'address': address, 'login': login}
        )

        await self.write_msg(RULES, writer=writer)
        await self.get_short_history(address)

        while True:
            msg: str = await self.read_msg(reader=reader)
            if not msg:
                break  # User disconnection
            elif msg.startswith(PRIVATE):
                await self.private_msg(msg, login, address)
            elif msg.startswith(CREATE):
                await self.create_chat(msg, login, writer)
            elif msg.startswith(JOIN):
                await self.join_chat(msg, login, writer)
            elif msg.startswith(CHAT):
                await self.join_chat(msg, login)
            elif msg == CHATS:
                await self.show_chats(login)
            else:
                msg_to_save: str = login + ': ' + msg
                self.short_history.append(msg_to_save)
                await self.public_msg(msg, login, address)

        self.delete_login_address(login, address)
        writer.close()

        logger.info(
            'Client %(login)s disconnected at %(address)s',
            {'address': address, 'login': login}
        )

    async def greeting_client(
            self, writer: StreamWriter, reader: StreamReader) -> str:
        """Greeting new clients on server."""
        await self.write_msg(GREETING, writer=writer)
        while True:
            answer: str = await self.read_msg(reader=reader)
            if answer == REGISTRATION:
                login: str = await self.registration(writer, reader)
                break
            elif answer == AUTHORIZATION:
                login: str = await self.authorization(writer, reader)
                break
            await self.write_msg(WRONG_COMMAND + RETRY, writer=writer)
        return login

    def check_if_registered(self, login: str, password: str = None) -> bool:
        """Checking if the user is registered and the password is correct"""
        # Checking if the user is registered:
        if login in self.login_password.keys():
            if not password:
                return True
            #  Checking if the password is correct:
            if password == self.login_password[login]:
                return True
        return False

    def fill_login_password(self, login: str, password: str) -> str:
        """
        Set or change user's password.
        """
        msg: str = ''
        if login not in self.login_password.keys():
            msg = REGISTERED
        else:
            msg = PASSWORED_CHANGED
            logger.info('User %(login)s changed password', {'login': login})
        self.login_password[login] = password
        return msg

    def delete_login_address(self, login: str, address: str) -> None:
        """
        Delete address from dictionary.
        Needed, when client is offline.
        """
        if login in self.login_address.keys():
            if address in self.login_address[login]:
                self.login_address[login].remove(address)

    def extend_login_address(self, login: str, address: str) -> None:
        """
        Add a new item in dict or add a new address in list,
        that is in dict's values.
        """
        if login not in self.login_address.keys():
            self.login_address[login] = [address]
        else:
            self.login_address[login].append(address)

    def get_clients_address(self, writer: StreamWriter) -> str:
        """
        Get client's address in format "HOST:PORT",
        using his StreamWriter().
        """
        address_tuple: tuple[str, int] = writer.get_extra_info('peername')
        address: str = address_tuple[0] + ':' + str(address_tuple[1])
        return address

    async def ask_for_login_password(
            self, writer: StreamWriter, reader: StreamReader) -> tuple[str]:
        """Ask user to enter his login and password"""

        await self.write_msg(LOGIN, writer=writer)
        login: str = await self.read_msg(reader=reader)

        if not login:
            login: str = ''
            password: str = ''
            return login, password

        await self.write_msg(PASSWORD, writer=writer)
        password: str = await self.read_msg(reader=reader)

        if not password:
            login: str = ''
            password: str = ''

        return login, password

    async def registration(self, writer: StreamWriter,
                           reader: StreamReader) -> str:
        """Register new users."""
        success: bool = False
        msg: str = ''

        while not success:

            login, password = await self.ask_for_login_password(writer, reader)

            if not login and not password:
                break

            if self.check_if_registered(login):
                msg = REGISTRATION_FAILED
                await self.write_msg(msg, writer=writer)
                authorization = await self.read_msg(reader=reader)
                if not authorization:
                    login = ''
                    break
                if authorization == AUTHORIZATION:
                    login = await self.authorization(writer, reader)
                    break
            else:
                msg = SUCCESSFULLY_REGISTERED
                await self.write_msg(msg, writer=writer)
                self.fill_login_password(login, password)
                address = self.get_clients_address(writer)
                self.extend_login_address(login, address)
                success = True
                logger.info('Successfully registrated user %(login)s',
                            {'login': login})
        return login

    async def authorization(self, writer: StreamWriter,
                            reader: StreamReader) -> None:
        """Authorizes registered users."""
        success: bool = False
        msg: str = ''

        while not success:

            login, password = await self.ask_for_login_password(writer, reader)

            if self.check_if_registered(login, password=password):
                msg = SUCCESSFULLY_AUTHORIZED
                await self.write_msg(msg, writer=writer)
                address = self.get_clients_address(writer)
                self.extend_login_address(login, address)
                success = True
                logger.info('Successfully authorized user %(login)s',
                            {'login': login})
            else:
                msg = AUTHORIZATION_FAILED
                await self.write_msg(msg, writer=writer)
                registration: str = await self.read_msg(reader=reader)
                if not registration:
                    login = ''
                    break
                if registration == REGISTRATION:
                    login = await self.registration(writer, reader)
                    break
        return login

    async def read_msg(
            self, address: str = None, reader: StreamReader = None) -> str:
        """
        Read new message.
        """
        if not reader and not address:
            logger.error('Reader did not read message')
            pass
        elif address and not reader:
            try:
                reader: StreamReader = self.address_writer_reader[address][1]
            except KeyError as error:
                logger.error(error)
                pass
        data: bytes = await reader.read(1024)
        if not data:
            msg: str = ''
            return msg
        msg: str = data.decode()
        return msg

    async def write_msg(self, msg: str, address: str = None,
                        writer: StreamWriter = None) -> None:
        """
        Write new message.
        """
        if address and not writer:
            try:
                writer: StreamWriter = self.address_writer_reader[address][0]
                writer.write(msg.encode())
                await writer.drain()
            except KeyError as error:
                logger.error(error)
                pass
        elif writer and not address:
            writer.write(msg.encode())
            await writer.drain()
        else:
            logger.error('Message "%(msg)s" is not delivered', {'msg': msg})

    async def public_msg(
            self, msg: str, current_login: str, current_address: str) -> None:
        """
        Write message in public chat.
        """
        for login in self.login_address.keys():
            for address in self.login_address[login]:
                if address != current_address:
                    if login == current_login:
                        msg_to_send = ME + ': ' + msg
                    else:
                        msg_to_send = current_login + ': ' + msg
                    await self.write_msg(msg_to_send, address=address)

    async def private_msg(
            self, msg: str, current_login: str, current_address: str) -> None:
        """
        Write message to certain person.
        """
        if PRIVATE in msg and ' ' in msg:
            msg: str = msg.replace(PRIVATE, '')
            login, msg = msg.split(' ', maxsplit=1)
            if login == current_login:
                # Msg to current user himself
                adresses: list[str] = self.login_address[login]
                for address in adresses:
                    if address != current_address:
                        msg_to_send: str = ME + ': ' + msg + ' | private msg'
                        await self.write_msg(msg_to_send, address=address)
            else:
                if login in self.login_address.keys():
                    recipient_adresses: list[str] = self.login_address[login]
                    for address in recipient_adresses:
                        msg_to_send: str = \
                            current_login + ': ' + msg + ' | private msg'
                        await self.write_msg(msg_to_send, address=address)
                    sender_adresses: list[str] = \
                        self.login_address[current_login]
                    for address in sender_adresses:
                        # Msg to current user other clients
                        if address != current_address:
                            msg_to_send: str = \
                                ME + ': ' + msg + ' | private msg'
                            await self.write_msg(msg_to_send, address=address)
                else:
                    msg_to_send: str = USERNAME + login + NOT_REGISTERED
                    await self.write_msg(msg_to_send, address=current_address)
        else:
            msg_to_send: str = WRONG_COMMAND
            await self.write_msg(msg_to_send, address=current_address)

    async def get_short_history(self, address: str) -> None:
        if self.short_history:
            await self.write_msg(HISTORY, address=address)
            for msg in self.short_history:
                await self.write_msg(msg + '\n', address=address)
        else:
            msg: str = EMPTY_HISTORY
            await self.write_msg(msg, address=address)


if __name__ == '__main__':
    server = Server()
    asyncio.run(server.start())
