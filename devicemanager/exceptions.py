from apps.check.logger import django_actions_logger


class BaseDeviceException(Exception):
    def __init__(self, message: str, ip: str = "no ip"):
        django_actions_logger.warning("%s %s", ip, message)
        self.message: str = message

    def __str__(self):
        return self.message


class AuthException(BaseDeviceException):
    pass


class DeviceException(BaseDeviceException):
    pass


class SSHConnectionError(DeviceException):
    def __init__(self, message: str, ip: str = "no ip", ssh_output: str = ""):
        """Store safe OpenSSH output used to inspect a changed host key."""

        super().__init__(message, ip=ip)
        self.ssh_output = ssh_output


class TelnetConnectionError(DeviceException):
    pass


class DeviceLoginError(DeviceException):
    pass


class UnknownDeviceError(DeviceException):
    pass
