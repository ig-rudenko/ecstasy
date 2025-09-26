from django.http import FileResponse
from django.utils.decorators import method_decorator
from rest_framework import exceptions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from check import models
from check.permissions import profile_permission
from gathering.services.configurations import (
    ConfigFileError,
    ConfigStorage,
    ConfigurationGather,
    LocalConfigStorage,
)

from ...models import Devices
from ..serializers import ConfigFileSerializer
from ..swagger import schemas
from .base import DeviceAPIView


class ConfigFilesPagination(PageNumberPagination):
    page_size = 25


class BaseConfigStorageAPIView(DeviceAPIView):
    config_storage: type[ConfigStorage] | None = None

    def get_storage(self, device: Devices, file_name: str | None = None) -> ConfigStorage:
        """
        ## Эта функция проверяет, что файл конфигурации верный.

        :param device: Устройство.
        :param file_name: Имя файла конфигурации (optional).
        :return: Хранилище для конфигураций.
        """

        if self.config_storage is None or not issubclass(self.config_storage, ConfigStorage):
            raise NotImplementedError("Хранилище конфигураций должно наследоваться от ConfigStorage")

        storage: ConfigStorage = self.config_storage(device)

        if file_name is None:
            return storage

        # Дополнительные проверки, если файл конфигурации был передан
        if not storage.validate_config_name(file_name):
            raise exceptions.ParseError("invalid file name")

        if not storage.is_exist(file_name):
            raise exceptions.NotFound("file not found")

        return storage


class DownloadDeleteConfigAPIView(BaseConfigStorageAPIView):
    """
    # Для загрузки и удаления файла конфигурации конкретного оборудования
    """

    config_storage = LocalConfigStorage

    @method_decorator(profile_permission(models.Profile.BRAS))
    def get(self, request, device_name_or_ip: str, file_name: str):
        """
        ## Отправляет содержимое файла конфигурации
        """
        device = self.get_object()
        storage = self.get_storage(device, file_name)
        return FileResponse(storage.open(file_name), filename=file_name)

    @method_decorator(profile_permission(models.Profile.BRAS))
    def delete(self, request, device_name_or_ip: str, file_name: str):
        """
        ## Удаляет файл конфигурации
        """
        device = self.get_object()
        self.get_storage(device, file_name).delete(file_name)
        return Response(status=204)


class ListDeviceConfigFilesAPIView(BaseConfigStorageAPIView):
    config_storage = LocalConfigStorage
    serializer_class = ConfigFileSerializer

    @schemas.config_files_list_api_doc
    @method_decorator(profile_permission(models.Profile.BRAS))
    def get(self, requests, *args, **kwargs):
        """
        ## Перечень файлов конфигураций указанного оборудования

        Пример ответа:

            [
                {
                    "name": "config_file_96f7d499c739875.txt",
                    "size": 19346,
                    "modTime": "11:53 28.03.2023",
                }
            ]
        """
        device = self.get_object()
        storage = self.get_storage(device)

        config_files = storage.files_list()
        serializer = self.serializer_class(config_files, many=True)

        return Response(serializer.data, status=200)


class CollectConfigAPIView(BaseConfigStorageAPIView):
    config_storage = LocalConfigStorage

    @method_decorator(profile_permission(models.Profile.BRAS))
    def post(self, request, *args, **kwargs):
        """
        ## В реальном времени смотрим и сохраняем конфигурацию оборудования

        Если такая конфигурация уже имеется, то файл не будет создан (чтобы не было лишних копий)

        """
        device = self.get_object()
        storage = self.get_storage(device)
        gather = ConfigurationGather(storage)

        try:
            if gather.collect_config_file():
                # Файл конфигурации был добавлен
                return Response({"status": "Была получена новая конфигурация"})
            else:
                # Файл конфигурации не потребовалось добавлять
                return Response(
                    {
                        "status": "Текущая конфигурация не отличается от последней сохраненной,"
                        " так что файл не был создан"
                    },
                    status=200,
                )

        except ConfigFileError as error:
            return Response({"error": error.message}, status=500)
