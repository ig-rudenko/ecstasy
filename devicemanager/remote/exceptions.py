from devicemanager.exceptions import BaseDeviceException


class RemoteDeviceException(BaseDeviceException):
    pass


class RemoteAuthenticationFailed(RemoteDeviceException):
    pass


class InvalidMethod(RemoteDeviceException):
    pass
