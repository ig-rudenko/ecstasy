from ecstasy_project.settings import django_actions_logger


class AuthException(Exception):
    def __init__(self, message: str):
        django_actions_logger.warning(message)
        self.message: str = message

    def __str__(self):
        return self.message


class DeviceException(Exception):
    def __init__(self, message: str):
        django_actions_logger.warning(message)
        self.message: str = message

    def __str__(self):
        return self.message


class TelnetConnectionError(DeviceException):
    pass


class TelnetLoginError(DeviceException):
    pass


class UnknownDeviceError(DeviceException):
    pass
