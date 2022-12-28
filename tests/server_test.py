import asyncio

import pytest

from constants import (ALREADY_IN_CHAT, AUTHORIZATION, AUTHORIZATION_FAILED,
                       CHANGE, CHAT_CREATED, CHAT_EXIST, CHAT_NOT_EXIST,
                       EMPTY_HISTORY, GREETING, HISTORY, LOGIN, MAXBYTES,
                       NO_CHAT, NOT_IN_CHAT, NOT_REGISTERED, PASSWORD,
                       PASSWORED_CHANGED, REGISTRATION, REGISTRATION_FAILED,
                       RULES, SUCCESSFULLY_AUTHORIZED, SUCCESSFULLY_REGISTERED,
                       USERNAME)


class TestServer:

    @pytest.mark.asyncio
    async def test_standart(self):
        """Testing user's standart behavior"""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                '127.0.0.1',
                8000)
        except ConnectionRefusedError:
            assert 'Server is not running', False
            return
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == GREETING

        # registration
        self.writer.write(REGISTRATION.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == LOGIN

        # input login
        self.writer.write('TestUser'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == PASSWORD

        # input password
        self.writer.write('TestPassword'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == SUCCESSFULLY_REGISTERED

        # rules + chat history
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == RULES + EMPTY_HISTORY

        # public msg
        self.writer.write('TestPublic'.encode())
        await self.writer.drain()

        # show empty list of chats
        self.writer.write('/chats'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == NO_CHAT

        # create chat
        self.writer.write('/create TestChat'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == CHAT_CREATED

        # create the same chat again
        self.writer.write('/create TestChat'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == CHAT_EXIST

        # show chats
        self.writer.write('/chats'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == '<Вы состоите в 1 чатах: >\nTestChat\n'

        # private message
        self.writer.write('@UnknowUser Hello'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == USERNAME + 'UnknowUser' + NOT_REGISTERED

        # change password
        new_password = CHANGE + ' NewTestPassword'
        self.writer.write(new_password.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == PASSWORED_CHANGED

    @pytest.mark.asyncio
    async def test_second_client(self):
        """Testing second client of existing user"""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                '127.0.0.1',
                8000)
        except ConnectionRefusedError:
            assert 'Server is not running', False
            return
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == GREETING

        # registration with existing login
        self.writer.write(REGISTRATION.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == LOGIN

        # input login
        self.writer.write('TestUser'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == PASSWORD

        # input password
        self.writer.write('TestPassword'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == REGISTRATION_FAILED

        # authorization with not existing login
        self.writer.write(AUTHORIZATION.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == LOGIN

        # input new login
        self.writer.write('NewTestUser'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == PASSWORD

        # input password
        self.writer.write('TestPassword'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == AUTHORIZATION_FAILED

        # authorization with existing login
        self.writer.write(AUTHORIZATION.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == LOGIN

        # input existing login
        self.writer.write('TestUser'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == PASSWORD

        # input existing password
        self.writer.write('NewTestPassword'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == SUCCESSFULLY_AUTHORIZED

        # rules + chat history
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == RULES + HISTORY + 'Я: TestPublic\n'

        # show chats
        self.writer.write('/chats'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == '<Вы состоите в 1 чатах: >\nTestChat\n'

        # join chat user already in
        self.writer.write('/join TestChat'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == ALREADY_IN_CHAT

        # join chat that doesn't exist
        self.writer.write('/join NewTestChat'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == \
            '<Чат "NewTestChat" не существует>\n' + CHAT_NOT_EXIST

    @pytest.mark.asyncio
    async def test_another_user(self):
        """Testing second user's behavior"""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                '127.0.0.1',
                8000)
        except ConnectionRefusedError:
            assert 'Server is not running', False
            return
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == GREETING

        # registration
        self.writer.write(REGISTRATION.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == LOGIN

        # input login
        self.writer.write('SecondTestUser'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == PASSWORD

        # input password
        self.writer.write('SecondTestPassword'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == SUCCESSFULLY_REGISTERED

        # rules + chat history
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == RULES + HISTORY + 'TestUser: TestPublic\n'

        # message to chat that the user is not a member of
        self.writer.write('/chat TestChat'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == NOT_IN_CHAT

        # join to existing chat
        self.writer.write('/join TestChat'.encode())
        await self.writer.drain()
        message = await self.reader.read(MAXBYTES)
        assert message.decode() == \
            '<Запрос на присоединение к чату "TestChat" ' \
            'был отправлен его администратору> \n'
