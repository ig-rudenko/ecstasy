import hashlib
import re

from typing import Union
from datetime import datetime

from django.db.models import Q
from django.http import FileResponse
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response

from ..permissions import DevicePermission
from check import models
from check.views import permission


class ConfigStorageMixin:
    @staticmethod
    def get_errors_for_config_path(
            device_folder: str, file_name: str = ""
    ) -> Union[Response, None]:

        storage = settings.CONFIG_STORAGE_DIR

        if not (storage / device_folder).exists():
            (storage / device_folder).mkdir(parents=True)

        if not file_name:
            return

        if ".." in file_name:
            return Response({"error": "Invalid file name"}, status=400)

        if not (storage / device_folder / file_name).exists():
            return Response({"error": "File does not exist"}, status=400)


@method_decorator(permission(models.Profile.BRAS), name="dispatch")
class DownloadDeleteConfigAPIView(APIView, ConfigStorageMixin):
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
        ## Открывает файл в двоичном режиме и возвращает объект FileResponse.

        :param request: Объект запроса
        :param device_name: str — это имя устройства, для которого предназначен файл конфигурации
        :param file_name: str — имя загружаемого файла
        :return: Объект ответа файла.
        """
        self.validate_device(device_name)

        config_path_errors = self.get_errors_for_config_path(device_name, file_name)
        if config_path_errors:
            return config_path_errors

        config_file = (settings.CONFIG_STORAGE_DIR / device_name / file_name).open("rb")
        return FileResponse(config_file, filename=file_name)

    def delete(self, request, device_name: str, file_name: str):
        """
        ## Удаляет файл из файловой системы
        """

        self.validate_device(device_name)

        config_path_errors = self.get_errors_for_config_path(device_name, file_name)
        if config_path_errors:
            return config_path_errors

        (settings.CONFIG_STORAGE_DIR / device_name / file_name).unlink(missing_ok=True)

        return Response(status=204)


@method_decorator(permission(models.Profile.BRAS), name="dispatch")
class ListDeviceConfigFilesAPIView(APIView, ConfigStorageMixin):

    def get(self, requests, device_name: str):
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

        # Создание пути к папке конфигурации для устройства.
        config_folder = settings.CONFIG_STORAGE_DIR / device_name

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
            res.append(
                {
                    "name": file.name,
                    "size": file.stat().st_size,  # Размер в байтах
                    "modTime": datetime.fromtimestamp(file.stat().st_mtime).strftime(
                        "%H:%M %d.%m.%Y"  # Время последней модификации
                    ),
                    "isDir": file.is_dir(),
                }
            )
        return res


@method_decorator(permission(models.Profile.BRAS), name="dispatch")
class CollectConfigAPIView(APIView):

    @staticmethod
    def get_last_config(device_name: str) -> str:
        """
        ## Возвращает последнюю конфигурацию устройства

        :param device_name: Имя устройства, с которого вы хотите получить последнюю конфигурацию
        """

        config_folder = settings.CONFIG_STORAGE_DIR / device_name
        if not config_folder.exists():
            config_folder.mkdir(parents=True)

        files = list(config_folder.iterdir())
        if not files:
            return ""

        # Поиск самого последнего измененного файла в каталоге.
        last_file = max(files, key=lambda file: file.stat().st_mtime)
        try:
            with last_file.open("r") as f:
                content = f.read()
        except UnicodeError:
            return ""
        return content

    def post(self, request, device_name: str):
        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(self.request, device)

        last_config = self.get_last_config(device_name)

        with device.connect() as session:
            if hasattr(session, "get_current_configuration"):
                current_config: str = session.get_current_configuration()
            else:
                return Response(
                    {"error": "This device can't collect configuration"}, status=400
                )

        # Берем текущую конфигурацию и удаляем все пробелы, а затем хешируем ее.
        current_config_hash = hashlib.sha3_224(
            re.sub(r"\s", "", current_config).encode()
        ).hexdigest()

        # Берем прошлую конфигурацию и удаляем все пробелы, а затем хешируем ее.
        last_config_hash = hashlib.sha3_224(
            re.sub(r"\s", "", last_config).encode()
        ).hexdigest()

        # Проверяем, совпадает ли last_config с current_config.
        if last_config_hash == current_config_hash:
            return Response(status=200)

        new_file_name = "config_file_" + current_config_hash[:15] + ".txt"
        file_path = settings.CONFIG_STORAGE_DIR / device_name / new_file_name

        with file_path.open("w", encoding="ascii") as file:
            file.write(current_config)

        return Response(status=201)
