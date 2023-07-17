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


class SSHConnectionError(DeviceException):
    pass


class TelnetConnectionError(DeviceException):
    pass


class DeviceLoginError(DeviceException):
    pass


class UnknownDeviceError(DeviceException):
    pass
