from django.conf import settings
from django.utils.module_loading import import_string

from .connector import RemoteDevice


class _DeviceRemoteConnector:
    def __init__(self):
        self._connector_class = RemoteDevice

    def set_connector(self, from_string: str):
        self._connector_class = import_string(from_string)

    @property
    def create(self) -> type[RemoteDevice]:
        return self._connector_class


remote_connector = _DeviceRemoteConnector()
remote_connector.set_connector(from_string=settings.REMOTE_DEVICE_CLASS)
