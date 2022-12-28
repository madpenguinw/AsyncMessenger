# Numerical values:
PORT: int = 8000
HOST: str = '127.0.0.1'
MAXLENGTH: int = 20
MAXBYTES: int = 4096

# Commands:
PRIVATE: str = '@'
DISCONNECT: str = '/disconnect'
REGISTRATION: str = '/register'
AUTHORIZATION: str = '/authorize'
CREATE: str = '/create'
JOIN: str = '/join'
ADD: str = '/add'
CHAT: str = '/chat'
EXIT: str = '/exit'
CHATS: str = '/chats'
CHANGE: str = '/change_password'


# Text
GREETING: str = (
    '\n<Добро пожаловать на сервер!> \n'
    f'<Введите "{REGISTRATION}" для регистрации или '
    f'"{AUTHORIZATION}" для авторизации> \n'
)

USER_EQ: str = 'user='
CHAT_EQ: str = 'chat='

RULES: str = (
    '<Правила:> \n'
    '<1 - Введите сообщение и оно отправится в общий чат> \n'
    '<2 - Чтобы отправить личное сообщение, напишите '
    f'"{PRIVATE}имя_пользователя" и через пробел введите свое сообщение> \n'
    f'<3 - Чтобы создать чат, введите "{CREATE} <название_чата>"> \n'
    '<4 - Чтобы добавить пользователя в чат, введите '
    f'"{ADD} {USER_EQ}<имя_пользователя> {CHAT_EQ}<название_чата>"> \n'
    f'<5 - Чтобы запросить доступ к чату, введите "{JOIN} <название_чата>"> \n'
    f'<6 - Чтобы подключиться к нему, введите "{CHAT} <название_чата>"> \n'
    f'<7 - Чтобы отключиться от чата, введите "{EXIT}"> \n'
    f'<8 - Чтобы узнать список своих чатов, введите "{CHATS}"> \n'
    f'<9 - Чтобы изменить пароль, введите "{CHANGE} <новый_пароль>". '
    'Пароль должен быть в одно слово> \n'
    f'<10 - Чтобы отключиться от сервера введите "{DISCONNECT}"> \n'
)

WRONG_COMMAND: str = '\n<Введена неверная команда>  \n'
RETRY: str = '<Повторите попытку> \n'

USERNAME: str = '\n<Пользователь с ником '
NOT_REGISTERED: str = ' не зарегистрирован на сервере>\n'

LOGIN: str = '\n<Введите свой логин>'
PASSWORD: str = '\n<Введите свой пароль>'
SUCCESSFULLY_REGISTERED: str = '\n<Вы были успешно зарегестрированы> \n'
SUCCESSFULLY_AUTHORIZED: str = '\n<Вы были успешно авторизованы> \n'

AUTHORIZATION_FAILED: str = (
    '\n<Данные введены неверно> \n'
    f'<Введите "{REGISTRATION}", чтобы зарегестрироваться> \n'
    '<Или введите любое другое значение, чтобы повторить попытку> \n'
)

REGISTRATION_FAILED: str = (
    '\n<Пользователь с таким именем уже зарегистрирован> \n'
    f'<Введите "{AUTHORIZATION}", чтобы авторизироваться> \n'
    '<Или введите любое другое значение, чтобы повторить попытку> \n'
)

EMPTY_HISTORY: str = '\n<История чата пуста> \n'
HISTORY: str = '\n<История чата>: \n'

REGISTERED: str = '\n<Регистрация прошла успешно> \n'
AUTHORIZED: str = '\n<Регистрация прошла успешно> \n'
PASSWORED_CHANGED: str = '\n<Пароль успешно изменен> \n'

ME: str = 'Я'

CHAT_EXIST: str = (
    '\n<Чат с данным названием уже существует> \n'
    '<Вы можете>: \n'
    f'<1 - запросить к нему доступ, введя "{JOIN} <название_чата>"> \n'
    f'<2 - подключиться к нему, введя "{CHAT} <название_чата>"> \n'
    f'<3 - узнать список своих чатов, введя "{CHATS}"> \n'
    f'<4 - создать другой чат, введя "{CREATE} <название_чата>"> \n'
    '<5 - Ввести любое другое сообщение. Оно отправится в общий чат> \n'
)

CHAT_CREATED: str = '\n<Чат был успешно создан>\n'

ALREADY_IN_CHAT: str = '<Вы уже состоите в этом чате>\n'

CHAT_NOT_EXIST: str = (
    f'<Вы можете создать его, введя "{CREATE} <название_чата>"> \n'
)

CLOSE = '> \n'
USER_SUCCESSFULLY_ADDED = '<Пользователь был успешно добавлен в чат '
YOU_SUCCESSFULLY_ADDED = '<Вы были успешно добавлены в чат '

ADDED_TO_CHAT: str = '<Вы были успешно добавлены в чат> \n'

CHAT_CONNECTED: str = (
    '\n<Вы вошли в приватный чат, все последующие сообщения '
    'будут отправляться в него> \n'
    '<Находясь здесь нельзя писать личные сообщения и добавлять '
    'новых пользователей в чаты> \n'
    f'<Чтобы выйти из приватного чата в общий, введите "{EXIT}"> \n'
)

NOT_IN_CHAT = (
    '<Вы не состоите в данном чате> \n'
    f'<Запросите к нему доступ, введя "{JOIN} <название_чата>"> \n'
)

NO_CHAT: str = '<Вы пока не состоите в чатах> \n'

DISCONNECT_FROM_CHAT: str = '<Вы покинули приватный чат> \n'
