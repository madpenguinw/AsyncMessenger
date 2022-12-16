import asyncio
import logging
from asyncio.streams import StreamReader, StreamWriter
from collections import deque

# импорт ниже используется, хоть и не подсвечен.
# Я импортирую в этот файл необходимый для логирования код из файла app_logger
import app_logger
from constants import (ADD, ALREADY_IN_CHAT, AUTHORIZATION,
                       AUTHORIZATION_FAILED, CHAT, CHAT_CONNECTED,
                       CHAT_CREATED, CHAT_EQ, CHAT_EXIST, CHAT_NOT_EXIST,
                       CHATS, CLOSE, CREATE, DISCONNECT_FROM_CHAT,
                       EMPTY_HISTORY, EXIT, GREETING, HISTORY, HOST, JOIN,
                       LOGIN, MAXBYTES, MAXLENGTH, ME, NO_CHAT, NOT_IN_CHAT,
                       NOT_REGISTERED, PASSWORD, PASSWORED_CHANGED, PORT,
                       PRIVATE, REGISTERED, REGISTRATION, REGISTRATION_FAILED,
                       RETRY, RULES, SUCCESSFULLY_AUTHORIZED,
                       SUCCESSFULLY_REGISTERED, USER_EQ,
                       USER_SUCCESSFULLY_ADDED, USERNAME, WRONG_COMMAND,
                       YOU_SUCCESSFULLY_ADDED)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
        login: str = await self.greeting_client(address)

        logger.info(
            'Client connected at %(address)s as %(login)s',
            {'address': address, 'login': login}
        )

        try:
            await self.write_msg_to_address(RULES, address)
        except Exception as error:
            logger.error(error)
        await self.get_short_history(login, address)

        while True:
            msg: str = await self.read_msg(address)
            if not msg:
                break  # User disconnection
            elif msg.startswith(PRIVATE):
                await self.private_msg(msg, login, address)
            elif msg.startswith(CREATE):
                await self.write_msg_to_myself(msg, address, login)
                await self.create_chat(msg, login)
            elif msg.startswith(JOIN):
                await self.write_msg_to_myself(msg, address, login)
                await self.join_chat(msg, login)
            elif msg.startswith(CHAT):
                await self.write_msg_to_myself(msg, address, login)
                await self.chat_msg(msg, login)
            elif msg == CHATS:
                await self.write_msg_to_myself(msg + '\n', address, login)
                await self.show_chats(login)
            elif msg.startswith(ADD) and ' ' + USER_EQ in msg \
                    and ' ' + CHAT_EQ in msg:
                await self.write_msg_to_myself(msg, address, login)
                await self.add_to_chat(msg, login)
            elif msg.startswith('/'):
                await self.write_msg_to_myself(msg, address, login)
                await self.write_msg_to_address(WRONG_COMMAND, address)
            else:
                msg_to_save: str = login + ': ' + msg
                self.short_history.append(msg_to_save)
                await self.public_msg(msg, login, address)

        self.delete_login_address(login, address)
        # Не понял ваш комментарий. Это и есть отдельный метод.
        # Он удаляет из отключившиеся клиенты пользователя из списка
        writer.close()

        logger.info(
            'Client %(login)s disconnected at %(address)s',
            {'address': address, 'login': login}
        )

    async def greeting_client(
            self, address) -> str:
        """Greeting new clients on server."""
        await self.write_msg_to_address(GREETING, address)
        while True:
            match answer := await self.read_msg(address):
                # Я сделал, как вы попросили, но в таком решении мне не нравятся два момента:
                # 1) в конструкции case я не могу использовать переменные, в частности REGISTRATION и AUTHORIZATION
                # 2) конструкция match мне подчеркивается линтером, хотя код при этом работает ¯\_(ツ)_/¯ 
                case '/register':
                    login: str = await self.registration(address)
                    break
                case '/authorize':
                    login = await self.authorization(address)
                    break
            await self.write_msg_to_address(WRONG_COMMAND + RETRY, address)
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
            self, address) -> tuple[str, str]:
        """Ask user to enter his login and password"""

        await self.write_msg_to_address(LOGIN, address)
        login: str = await self.read_msg(address)
        password: str = ''

        if not login:
            return login, password

        await self.write_msg_to_address(PASSWORD, address)
        password = await self.read_msg(address)

        return login, password

    async def registration(self, address: str) -> str:
        """Register new users."""
        success: bool = False
        msg: str = ''

        while not success:

            login: str = ''
            password: str = ''

            login, password = await self.ask_for_login_password(address)

            if not login and not password:
                break

            if self.check_if_registered(login):
                msg = REGISTRATION_FAILED
                await self.write_msg_to_address(msg, address)
                authorization = await self.read_msg(address)
                if not authorization:
                    login = ''
                    break
                if authorization == AUTHORIZATION:
                    login = await self.authorization(address)
                    break
            else:
                msg = SUCCESSFULLY_REGISTERED
                await self.write_msg_to_address(msg, address)
                self.fill_login_password(login, password)
                self.extend_login_address(login, address)
                success = True
                logger.info('Successfully registrated user %(login)s',
                            {'login': login})
        return login

    async def authorization(self, address: str) -> str:
        """Authorizes registered users."""
        success: bool = False
        msg: str = ''

        while not success:

            login, password = await self.ask_for_login_password(address)

            if self.check_if_registered(login, password=password):
                msg = SUCCESSFULLY_AUTHORIZED
                await self.write_msg_to_address(msg, address)
                self.extend_login_address(login, address)
                success = True
                logger.info('Successfully authorized user %(login)s',
                            {'login': login})
            else:
                msg = AUTHORIZATION_FAILED
                await self.write_msg_to_address(msg, address)
                registration: str = await self.read_msg(address)
                if not registration:
                    login = ''
                    break
                if registration == REGISTRATION:
                    login = await self.registration(address)
                    break
        return login

    async def create_chat(
            self, msg: str, login: str) -> None:
        """User can create chat and become its admin."""
        chat: str = msg.split(' ', maxsplit=1)[1]
        if chat in self.chat_logins.keys():
            logger.info('User "%(login)s" tried to create existing '
                        'chat "%(chat)s"', {'login': login, 'chat': chat})
            await self.write_msg(CHAT_EXIST, login)
        else:
            # first element in tuple -> chat admin
            self.chat_logins[chat] = (login, [login])
            if login not in self.login_chats.keys():
                self.login_chats[login] = []
            self.login_chats[login].append(chat)
            await self.write_msg(CHAT_CREATED, login)
            logger.info('User "%(login)s" created chat "%(chat)s"',
                        {'login': login, 'chat': chat})

    async def join_chat(self, msg: str, login: str) -> None:
        """Send to admin a request for joining to chat."""
        chat: str = msg.split(' ', maxsplit=1)[1]
        if chat in self.chat_logins.keys():
            if login in self.chat_logins[chat][1]:
                await self.write_msg(ALREADY_IN_CHAT, login)
            else:
                admin = self.chat_logins[chat][0]
                if admin in self.login_address.keys() and \
                        self.login_address[admin]:
                    await self.write_msg(
                        (
                            f'<Пользователь "{login}" хочет присоединиться '
                            f'к чату "{chat}">'
                        ),
                        admin
                    )
                    await self.write_msg(
                        f'<Введите "{ADD}{USER_EQ}{login} {CHAT_EQ}'
                        f'{chat}" чтобы добавить пользователя в чат> \n',
                        admin
                    )
                    await self.write_msg(
                        f'<Запрос на присоединение к чату "{chat}" '
                        'был отправлен его администратору> \n',
                        login
                    )
                else:
                    await self.write_msg(
                        (
                            f'<Администратор чата "{chat}" отсутствует на '
                            'сервере. Попробуйте повторить запрос позже> \n'
                        ),
                        login
                    )

        else:
            await self.write_msg(f'<Чат {chat} не существует> \n', login)

    async def add_to_chat(self, msg: str, admin: str) -> None:
        """Add user to chat."""
        user_chat: str = msg.split(USER_EQ, maxsplit=1)[1]
        user: str = user_chat.split(' ' + CHAT_EQ, maxsplit=1)[0]
        chat: str = user_chat.split(CHAT_EQ, maxsplit=1)[1]
        if user in self.login_address.keys() and \
                chat in self.chat_logins.keys():
            if self.chat_logins[chat][0] == admin:
                if user not in self.login_chats.keys():
                    self.login_chats[user] = []
                self.login_chats[user].append(chat)
                self.chat_logins[chat][1].append(user)
                await self.write_msg(
                    USER_SUCCESSFULLY_ADDED + f'"{chat}"' + CLOSE, admin)
                await self.write_msg(
                    YOU_SUCCESSFULLY_ADDED + f'"{chat}"' + CLOSE, user)
                logger.info(
                    'User "%(user)s" was added to chat '
                    '"%(chat)s" by %(admin)s',
                    {'user': user, 'chat': chat, 'admin': admin}
                )

    async def chat_msg(self, msg: str, login: str) -> None:
        """Send all messages of a user to a private chat."""
        chat_msg: str = ''
        chat: str = msg.split(' ', maxsplit=1)[1]
        if chat in self.chat_logins.keys():
            if login in self.chat_logins[chat][1]:
                await self.write_msg(CHAT_CONNECTED, login)
                logger.info(
                    'User "%(login)s" connected to private chat '
                    '"%(chat)s"',
                    {'login': login, 'chat': chat}
                )

                for address in self.login_address[login]:
                    while chat_msg != EXIT:

                        chat_msg = await self.read_msg(address)

                        if not chat_msg:
                            logger.error(
                                'KeyboardInterrupt: login=%(login)s',
                                {'login': login}
                            )
                            break

                        if chat_msg == EXIT:
                            break

                        msg_to_chat = login + ': ' + chat_msg + \
                            ' | private chat ' + chat
                        for user in self.chat_logins[chat][1]:
                            if user != login:
                                if self.login_address[user]:
                                    await self.write_msg(msg_to_chat, user)

                        msg_to_myself = ME + ': ' + chat_msg + \
                            ' | private chat ' + chat
                        await self.write_msg_to_myself(
                            msg_to_myself, address, login
                        )

                await self.write_msg(
                    DISCONNECT_FROM_CHAT,
                    login
                )
                logger.info(
                    'User "%(login)s" disconnected from private '
                    'chat "%(chat)s"',
                    {'login': login, 'chat': chat}
                )

            else:
                await self.write_msg(NOT_IN_CHAT, login)
        else:
            await self.write_msg(CHAT_NOT_EXIST, login)

    async def show_chats(self, login: str):
        """Shows all chats the user is a member of"""

        if login not in self.login_chats.keys() or not self.login_chats[login]:
            self.login_chats[login] = []
            await self.write_msg(NO_CHAT, login)
            return

        length = len(self.login_chats[login])
        answer: str = f'<Вы состоите в {length} чатах: >'
        for chat in self.login_chats[login]:
            answer += '\n' + chat
        answer += '\n'
        await self.write_msg(answer, login)

    async def read_msg(
            self, address: str) -> str:
        """
        Read new message.
        """
        answer: str = ''
        try:
            reader: StreamReader = \
                self.address_writer_reader[address][1]
            data: bytes = await reader.read(MAXBYTES)
            if not data:
                logger.error('Reader did not read message')
                pass
            answer = data.decode()
        except Exception as error:
            logger.error(error)
            pass

        return answer

    async def write_msg_to_address(self, msg: str, address: str) -> None:
        writer: StreamWriter = self.address_writer_reader[address][0]
        writer.write(msg.encode())
        await writer.drain()

    async def write_msg(self, msg: str, login: str) -> None:
        """
        Write new message.
        """
        if login in self.login_address.keys():
            for address in self.login_address[login]:
                await self.write_msg_to_address(msg, address)

    async def write_msg_to_myself(
            self, msg: str, current_address: str, login: str) -> None:
        addresses: list[str] = self.login_address[login]
        for address in addresses:
            if address != current_address:
                await self.write_msg_to_address(msg, address)

    async def public_msg(
            self, msg: str, current_login: str, current_address: str) -> None:
        """
        Write message in public chat.
        """
        for login in self.login_address.keys():
            if login == current_login:
                msg_to_myself = ME + ': ' + msg + ' | public chat'
                await self.write_msg_to_myself(
                    msg_to_myself, current_address, login
                )
            else:
                msg_to_all = current_login + ': ' + msg + ' | public chat'
                await self.write_msg(
                    msg_to_all, login
                )

    async def private_msg(
            self, msg: str, current_login: str, current_address: str) -> None:
        """
        Write message to certain person.
        """
        if PRIVATE in msg and ' ' in msg:
            string: str = msg.replace(PRIVATE, '')
            login, clear_msg = string.split(' ', maxsplit=1)
            if login == current_login:
                # Chatting to myself
                msg_to_myself: str = ME + ': ' + clear_msg + ' | private msg'
                await self.write_msg_to_myself(
                    msg_to_myself, current_address, login)
            else:
                if login in self.login_address.keys():
                    msg_to_send: str = \
                        current_login + ': ' + clear_msg + ' | private msg'
                    await self.write_msg(msg_to_send, login)
                    msg_to_myself = \
                        ME + ': ' + clear_msg + ' | private msg'
                    # Writing also to other client of user
                    await self.write_msg_to_myself(
                        msg_to_myself, current_address, current_login)

                else:
                    await self.write_msg_to_myself(
                        msg, current_address, current_login
                    )
                    msg_to_send = USERNAME + login + NOT_REGISTERED
                    await self.write_msg(msg_to_send, current_login)
        else:
            await self.write_msg_to_myself(msg, current_address, current_login)
            await self.write_msg(WRONG_COMMAND, current_login)

    async def get_short_history(self, login: str, address: str) -> None:
        """Shows last messages in public chat."""
        if self.short_history:
            await self.write_msg_to_address(HISTORY, address)
            for msg in self.short_history:
                if login in msg:
                    msg = msg.replace(login, ME)
                await self.write_msg_to_address(msg + '\n', address)
        else:
            msg = EMPTY_HISTORY
            await self.write_msg_to_address(msg, address)


if __name__ == '__main__':
    server = Server()
    asyncio.run(server.start())
