
# Numerical values:
PORT: int = 8000
HOST: str = '127.0.0.1'
MAXLENGTH: int = 20

# Commands:
PRIVATE: str = '@'
DISCONNECT: str = '/disconnect'
REGISTRATION: str = '/register'
AUTHORIZATION: str = '/authorize'

# Text
GREETING: str = (
    '\n<Добро пожаловать на сервер!> \n'
    f'<Введите "{REGISTRATION}" для регистрации или '
    f'"{AUTHORIZATION}" для авторизации> \n'
)

RULES: str = (
    '<Введите сообщение и оно отправится в общий чат> \n'
    f'<Чтобы отправить личное сообщение, напишите "{PRIVATE}имя_пользователя" '
    'и через пробел введите свое сообщение> \n'
    f'<Чтобы отключиться от сервера введите "{DISCONNECT}"> \n'
)

WRONG_COMMAND: str = '\n<Введена неверная команда>  \n'
RETRY: str = '<Повторите попытку> \n'

USERNAME: str = '\n<Пользователь с ником '
NOT_REGISTERED: str = ' не зарегистрирован на сервере>'

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
    f'<Введите "{AUTHORIZATION}", чтобы зарегестрироваться> \n'
    '<Или введите любое другое значение, чтобы повторить попытку> \n'
)

EMPTY_CHAT: str = '\n<История чата пуста> \n'
CHAT: str = '\n<История чата загружена> \n\n'

REGISTERED: str = '\n<Регистрация прошла успешно> \n'
AUTHORIZED: str = '\n<Регистрация прошла успешно> \n'
PASSWORED_CHANGED: str = '\n<Пароль успешно изменен> \n'

ME: str = 'Я'
