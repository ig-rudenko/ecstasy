from typing import Union
from datetime import datetime

from django.db.models import Q
from django.http import FileResponse
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from check import models
from check.views import permission
from devicemanager.vendors import BaseDevice

from gathering.collectors import ConfigurationGather
from ..permissions import DevicePermission
from ..filters import DeviceFilter
from ..serializers import DevicesSerializer


class ConfigStorageMixin:
    @staticmethod
    def get_errors_for_config_path(device_folder: str, file_name: str = ""):

        storage = settings.CONFIG_STORAGE_DIR / device_folder

        storage.mkdir(parents=True, exist_ok=True)

        if not file_name:
            return

        if ".." in file_name:
            return Response({"error": "Invalid file name"}, status=400)

        if not (storage / file_name).exists():
            return Response({"error": "File does not exist"}, status=400)


@method_decorator(permission(models.Profile.BRAS), name="get")
@method_decorator(permission(models.Profile.BRAS), name="delete")
class DownloadDeleteConfigAPIView(APIView, ConfigStorageMixin):
    """
    # Для загрузки и удаления файла конфигурации конкретного оборудования
    """

    permission_classes = [DevicePermission]

    def validate_device(self, device_name: str) -> None:
        """
        ## Эта функция проверяет, что имя устройства является допустимым

        :param device_name: Имя устройства для проверки
        :type device_name: str
        """
        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(self.request, device)

    def get(self, request, device_name: str, file_name: str):
        """
        ## Отправляет содержимое файла конфигурации
        """
        self.validate_device(device_name)

        # Метод, переводящий русские символы в транслитерацию в имени устройства.
        folder_name = BaseDevice.clear_description(device_name)

        config_path_errors = self.get_errors_for_config_path(folder_name, file_name)
        if config_path_errors:
            return config_path_errors

        config_file = (settings.CONFIG_STORAGE_DIR / folder_name / file_name).open("rb")
        return FileResponse(config_file, filename=file_name)

    def delete(self, request, device_name: str, file_name: str):
        """
        ## Удаляет файл конфигурации
        """

        self.validate_device(device_name)

        # Метод, переводящий русские символы в транслитерацию в имени устройства.
        folder_name = BaseDevice.clear_description(device_name)

        config_path_errors = self.get_errors_for_config_path(folder_name, file_name)
        if config_path_errors:
            return config_path_errors

        (settings.CONFIG_STORAGE_DIR / folder_name / file_name).unlink(missing_ok=True)

        return Response(status=204)


@method_decorator(permission(models.Profile.BRAS), name="get")
class ListDeviceConfigFilesAPIView(GenericAPIView, ConfigStorageMixin):
    permission_classes = [DevicePermission]

    def get(self, requests, device_name: str):
        """
        ## Перечень файлов конфигураций указанного оборудования

        Пример ответа:

            {
                "files": [
                    {
                        "name": "config_file_96f7d499c739875.txt",
                        "size": 19346,
                        "modTime": "11:53 28.03.2023",
                        "isDir": false
                    }
                ],

                ...

            }

        """

        # Получение ошибок для пути конфигурации.
        config_path_errors = self.get_errors_for_config_path(device_name)
        # Проверка, является ли config_path_errors пустым или нет.
        if config_path_errors:
            return config_path_errors

        # Получение объекта устройства из базы данных.
        device = get_object_or_404(models.Devices, name=device_name)
        # Проверка наличия у пользователя прав на устройство.
        self.check_object_permissions(self.request, device)

        return Response({"files": self.get_config_files(device_name)}, status=200)

    @staticmethod
    def get_config_files(device_name: str) -> list:
        """
        ## Возвращает список словарей, каждый из которых содержит информацию о файле в каталоге

        :param device_name: имя устройства, для которого мы хотим получить файлы конфигурации
        :return: Список словарей.
        """

        # Метод, который переводит русские символы в транслит в имени устройства.
        folder_name = BaseDevice.clear_description(device_name)

        # Создание пути к папке конфигурации для устройства.
        config_folder = settings.CONFIG_STORAGE_DIR / folder_name

        # Проверка, является ли config_folder файлом.
        if config_folder.is_file():
            config_folder.unlink()

        # Проверяем, существует ли папка config_folder. Если он не существует, он его создаст.
        if not config_folder.exists():
            config_folder.mkdir(parents=True)

        res = []

        files = sorted(
            config_folder.iterdir(),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        # Итерируемся по всем файлам и поддиректориям в директории
        for file in files:
            # Получение статистики файла.
            stats = file.stat()
            res.append(
                {
                    "name": file.name,
                    "size": stats.st_size,  # Размер в байтах
                    "modTime": datetime.fromtimestamp(stats.st_mtime).strftime(
                        "%H:%M %d.%m.%Y"  # Время последней модификации
                    ),
                    "isDir": file.is_dir(),
                }
            )
        return res


@method_decorator(permission(models.Profile.BRAS), name="get")
class ListAllConfigFilesAPIView(ListDeviceConfigFilesAPIView):
    """
    # Смотрим список оборудования и файлы конфигураций
    """

    filter_backends = [DjangoFilterBackend]
    filterset_class = DeviceFilter

    def get_queryset(self):
        """
        ## Возвращаем queryset всех устройств из доступных для пользователя групп
        """

        # Фильтруем запрос
        group_ids = self.request.user.profile.devices_groups.all().values_list(
            "id", flat=True
        )
        return models.Devices.objects.filter(group_id__in=group_ids).select_related(
            "group"
        )

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
                                "isDir": false,
                            }
                        ],
                    },

                    ...

                ],
            }

        """

        result = {
            "count": 0,
            "devices": [],
        }
        devices = self.filter_queryset(self.get_queryset())
        for dev in devices:
            result["count"] += 1
            serializer = DevicesSerializer(dev)
            result["devices"].append(
                {
                    **serializer.data,
                    "files": self.get_config_files(dev.name),
                }
            )

        return Response(result)


@method_decorator(permission(models.Profile.BRAS), name="dispatch")
class CollectConfigAPIView(APIView):
    def post(self, request, device_name: str):
        """
        ## В реальном времени смотрим и сохраняем конфигурацию оборудования

        Если такая конфигурация уже имеется, то файл не будет создан (чтобы не было лишних копий)

        """

        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(self.request, device)

        gather = ConfigurationGather(device)
        if gather.collect_config_file():
            status = 201
        else:
            status = 200
        return Response(status=status)
