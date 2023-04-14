import pathlib
import shutil
from datetime import datetime

from django.test import TestCase
from ..config_storage import LocalConfigStorage, ConfigFile
from check.models import Devices


class TestLocalStorage(TestCase):
    device_name = "device_name"
    storage_path = "./test_storage"

    def tearDown(self) -> None:
        shutil.rmtree("./test_storage", ignore_errors=True)

    def test_storage_init(self):
        dev = Devices.objects.create(ip="10.10.10.10", name=self.device_name)
        with self.settings(CONFIG_STORAGE_DIR=pathlib.Path(self.storage_path)):
            storage = LocalConfigStorage(dev)

            self.assertTrue(pathlib.Path(f"{self.storage_path}/{dev.name}").exists())

            self.assertFalse(storage.validate_config_name("./../folder/"))

            self.assertFalse(storage.is_exist("config.txt"))

    def test_add_remove_file(self):
        dev = Devices.objects.create(ip="10.10.10.10", name=self.device_name)
        with self.settings(CONFIG_STORAGE_DIR=pathlib.Path(self.storage_path)):
            storage = LocalConfigStorage(dev)

            configuration = "some config"
            config_name = "new_config.txt"

            # Добавляем файл
            self.assertTrue(storage.add(new_file_name=config_name, file_content=configuration))

            # Проверяем, что файл добавился
            file_path = pathlib.Path(f"{self.storage_path}/{dev.name}/{config_name}")
            self.assertTrue(file_path.exists())
            self.assertTrue(storage.is_exist(config_name))

            # Проверяем содержимое файла
            with file_path.open("r") as f, storage.open(config_name, mode="r") as sf:
                self.assertEqual(f.read(), sf.read())

            # Смотрим содержимое папки
            files_list = storage.files_list()

            # В хранилище должен быть 1 файл
            self.assertTrue(len(files_list), 1)

            file_stats = file_path.stat()
            # Смотрим правильный формат
            self.assertEqual(
                files_list[0],
                ConfigFile(
                    name=config_name,
                    size=file_stats.st_size,
                    # Время последней модификации
                    modTime=datetime.fromtimestamp(file_stats.st_mtime).strftime("%H:%M %d.%m.%Y"),
                    isDir=False,
                ),
            )

            # Удаляем файл
            self.assertTrue(storage.delete(config_name))

            # Теперь нет файлов
            self.assertEqual(storage.files_list(), [])
            self.assertFalse(storage.is_exist(config_name))

            # В хранилище тоже
            self.assertFalse(file_path.exists())

    def test_add_file_from_path(self):
        dev = Devices.objects.create(ip="10.10.10.10", name=self.device_name)
        with self.settings(CONFIG_STORAGE_DIR=pathlib.Path(self.storage_path)):
            storage = LocalConfigStorage(dev)

            config_file_path = pathlib.Path("./manage.py")
            config_name = "new_config.txt"

            # Если не передаем данные, то ничего не будет добавлено
            self.assertFalse(storage.add(config_name))

            # Передаем конфигурацию как путь к файлу
            self.assertTrue(storage.add(config_name, file_path=config_file_path))

            # Файл конфигурации в хранилище
            new_config_file_path = pathlib.Path(storage._storage / config_name)
            # Проверяем, что файл добавился
            self.assertTrue(new_config_file_path.exists())
            self.assertTrue(storage.is_exist(config_name))

            # Проверяем содержимое файла
            with new_config_file_path.open("rb") as f, storage.open(config_name, mode="rb") as sf:
                self.assertEqual(f.read(), sf.read())

            # Смотрим содержимое папки
            files_list = storage.files_list()

            # Должен быть 1 файл
            self.assertTrue(len(files_list), 1)
            file_stats = new_config_file_path.stat()

            # Смотрим правильный формат
            self.assertEqual(
                files_list[0],
                ConfigFile(
                    name=config_name,
                    size=file_stats.st_size,
                    # Время последней модификации
                    modTime=datetime.fromtimestamp(file_stats.st_mtime).strftime("%H:%M %d.%m.%Y"),
                    isDir=False,
                ),
            )
