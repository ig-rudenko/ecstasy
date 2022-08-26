class CommonException(Exception):
    def __init__(self, message: str):
        self.message: str = message

    def __str__(self):
        return self.message


class AuthException(CommonException):
    pass


class ConfigError(CommonException):
    pass
