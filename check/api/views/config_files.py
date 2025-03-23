from typing import Type

from django.http import FileResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import exceptions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from check import models
from check.permissions import profile_permission
from gathering.services.configurations import (
    ConfigurationGather,
    ConfigFileError,
    LocalConfigStorage,
    ConfigStorage,
)
from .base import DeviceAPIView
from ..filters import DeviceFilter
from ..serializers import DevicesSerializer, ConfigFileSerializer
from ..swagger import schemas


class ConfigFilesPagination(PageNumberPagination):
    page_size = 25


class BaseConfigStorageAPIView(DeviceAPIView):
    config_storage: Type[ConfigStorage] | None = None

    def get_storage(self, device: str, file_name: str | None = None) -> ConfigStorage:
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


@method_decorator(profile_permission(models.Profile.BRAS), name="dispatch")
class DownloadDeleteConfigAPIView(BaseConfigStorageAPIView):
    """
    # Для загрузки и удаления файла конфигурации конкретного оборудования
    """

    config_storage = LocalConfigStorage

    def get(self, request, device_name: str, file_name: str):
        """
        ## Отправляет содержимое файла конфигурации
        """
        device = self.get_object()
        storage = self.get_storage(device.name, file_name)
        return FileResponse(storage.open(file_name), filename=file_name)

    def delete(self, request, device_name: str, file_name: str):
        """
        ## Удаляет файл конфигурации
        """
        device = self.get_object()
        self.get_storage(device.name, file_name).delete(file_name)
        return Response(status=204)


@method_decorator(profile_permission(models.Profile.BRAS), name="get")
class ListDeviceConfigFilesAPIView(BaseConfigStorageAPIView):
    config_storage = LocalConfigStorage
    serializer_class = ConfigFileSerializer

    @schemas.config_files_list_api_doc
    def get(self, requests, device_name: str):
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
        storage = self.get_storage(device.name)

        config_files = storage.files_list()
        serializer = self.serializer_class(config_files, many=True)

        return Response(serializer.data, status=200)


@method_decorator(cache_page(60 * 10), name="dispatch")
@method_decorator(vary_on_headers("Authorization"), name="dispatch")
@method_decorator(profile_permission(models.Profile.BRAS), name="dispatch")
@method_decorator(schemas.devices_config_files_list_api_doc, name="get")
class ListAllConfigFilesAPIView(BaseConfigStorageAPIView):
    """
    # Смотрим список оборудования и файлы конфигураций
    """

    filter_backends = [DjangoFilterBackend]
    filterset_class = DeviceFilter
    config_storage = LocalConfigStorage
    serializer_class = ConfigFileSerializer
    pagination_class = ConfigFilesPagination

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        all_fields = DevicesSerializer.Meta.fields.copy()
        return_fields = self.request.GET.get("return-fields", "").split(",")
        return_fields = list(set(return_fields) & set(all_fields))

        if not return_fields:
            return_fields = all_fields

        if "group" in return_fields:
            queryset = queryset.select_related("group")

        queryset = queryset.values(*return_fields)
        return queryset

    def get(self, request, **kwargs):
        """

        ## Перечень оборудования и файлы конфигураций

        Пример ответа:

            {
                "count": 948,
                "devices": [
                    {
                        "ip": "172.30.0.58",
                        "name": "FTTB_Aktybinsk42_p1_TKD_116",
                        "vendor": "D-Link",
                        "group": "ASW",
                        "model": "DES-3200-28",
                        "port_scan_protocol": "telnet",
                        "files": [
                            {
                                "name": "config_file_96f7d499c739875.txt",
                                "size": 19346,
                                "modTime": "11:53 28.03.2023",
                            }
                        ],
                    },

                    ...

                ],
            }

        """

        result = []

        qs = self.filter_queryset(self.get_queryset())
        devices = self.paginate_queryset(qs)
        for dev in devices:
            # Файлы конфигураций
            files = self.get_storage(dev["name"]).files_list()
            # Сериализуем файлы
            files_serializer = self.serializer_class(files, many=True)

            # Форматируем название группы
            if dev.get("group__name"):
                dev["group"] = dev["group__name"]
                del dev["group__name"]

            result.append(
                {
                    **dev,
                    "files": files_serializer.data,
                }
            )

        return self.get_paginated_response(result)


@method_decorator(profile_permission(models.Profile.BRAS), name="dispatch")
class CollectConfigAPIView(BaseConfigStorageAPIView):
    config_storage = LocalConfigStorage

    def post(self, request, device_name: str):
        """
        ## В реальном времени смотрим и сохраняем конфигурацию оборудования

        Если такая конфигурация уже имеется, то файл не будет создан (чтобы не было лишних копий)

        """
        device = self.get_object()
        storage = self.get_storage(device.name)
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
