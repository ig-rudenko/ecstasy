class AuthException(Exception):
    def __init__(self, message: str):
        self.message: str = message

    def __str__(self):
        return self.message


class TelnetConnectionError(Exception):
    def __init__(self, message: str):
        self.message: str = message

    def __str__(self):
        return self.message


class TelnetLoginError(Exception):
    def __init__(self, message: str):
        self.message: str = message

    def __str__(self):
        return self.message


class UnknownDeviceError(Exception):
    def __init__(self, message: str):
        self.message: str = message

    def __str__(self):
        return self.message
