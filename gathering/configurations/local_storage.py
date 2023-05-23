import pathlib
import shutil
from datetime import datetime
from typing import IO, List

from django.conf import settings

from check import models
from .base import ConfigStorage, ConfigFile


class LocalConfigStorage(ConfigStorage):
    """
    # Локальное хранилище для файлов конфигураций в директории
    """

    def __init__(self, device: models.Devices):
        self.device = device

        # Создание пути к каталогу, в котором хранятся файлы конфигурации.
        self._storage = pathlib.Path()
        self.check_storage()

    def storage_path(self):
        return self._storage

    def check_storage(self) -> bool:
        # Проверяем наличие переменной
        if not settings.CONFIG_STORAGE_DIR or not isinstance(
            settings.CONFIG_STORAGE_DIR, pathlib.Path
        ):
            raise ValueError(
                "Укажите CONFIG_STORAGE_DIR в settings.py как объект `pathlib.Path`"
                " для использования локального хранилища конфигураций"
            )
        self._storage = settings.CONFIG_STORAGE_DIR / self.slug_name(self.device.name)
        # Создаем папку, если надо
        if not self._storage.exists():
            self._storage.mkdir(parents=True)
        return True

    def validate_config_name(self, file_name: str) -> bool:
        if ".." in file_name or (self._storage / file_name).is_dir():
            return False

        return True

    def is_exist(self, file_name: str) -> bool:
        if not (self._storage / file_name).exists():
            return False
        return True

    def open(self, file_name: str, mode: str = "rb", **kwargs) -> IO:
        return (self._storage / file_name).open(mode, **kwargs)

    def delete(self, file_name: str) -> bool:
        (self._storage / file_name).unlink(missing_ok=True)
        return True

    def add(self, new_file_name: str, file_content=None, file_path: pathlib.Path = None) -> bool:

        # Если ничего не передали
        if not file_content and not file_path:
            return False

        # Если передали только путь к файлу
        elif not file_content and file_path:
            new_file_path = self._storage / new_file_name

            # Если это один и тот же файл
            if file_path == new_file_path:
                return True

            # Открываем переданный файл (чтение) и новый (запись)
            with file_path.open("rb") as source_file, new_file_path.open("wb") as dest_file:
                # Копируем содержимое файла
                shutil.copyfileobj(source_file, dest_file)
            file_path.unlink()  # И удаляем старый файл
            return True

        # Выбираем флаги для записи
        if isinstance(file_content, str):
            mode = "w"
        else:
            mode = "wb"

        # Сохраняем файл
        with (self._storage / new_file_name).open(mode) as file:
            file.write(file_content)
        return True

    def files_list(self) -> List[ConfigFile]:
        config_files = sorted(
            self._storage.iterdir(),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )
        res = []
        # Итерируемся по всем файлам и поддиректориям в директории
        for file in config_files:
            if file.is_dir():
                # Пропускаем папки
                continue
            # Получение статистики файла.
            stats = file.stat()
            res.append(
                ConfigFile(
                    name=file.name,
                    size=stats.st_size,  # Размер в байтах
                    modTime=datetime.fromtimestamp(stats.st_mtime).strftime(
                        "%H:%M %d.%m.%Y"  # Время последней модификации
                    ),
                )
            )
        return res
