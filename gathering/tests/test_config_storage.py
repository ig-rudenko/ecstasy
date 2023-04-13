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

    def test_add_file_to_storage(self):
        dev = Devices.objects.create(ip="10.10.10.10", name=self.device_name)
        with self.settings(CONFIG_STORAGE_DIR=pathlib.Path(self.storage_path)):
            storage = LocalConfigStorage(dev)

            configuration = "some config"
            config_name = "new_config.txt"

            storage.add(new_file_name=config_name, file_content=configuration)

            # Проверяем, что файл добавился
            file_path = pathlib.Path(f"{self.storage_path}/{dev.name}/{config_name}")
            self.assertTrue(file_path.exists())
            self.assertTrue(storage.is_exist(config_name))

            # Проверяем содержимое файла
            with file_path.open("r") as f, storage.open(config_name, mode="r") as sf:
                self.assertEqual(f.read(), sf.read())

            # Смотрим содержимое папки
            files_list = storage.files_list()
            file_stats = file_path.stat()
            # Смотрим правильный формат
            self.assertEqual(
                files_list[0],
                ConfigFile(
                    name=config_name,
                    size=file_stats.st_size,
                    modTime=datetime.fromtimestamp(file_stats.st_mtime).strftime(
                        "%H:%M %d.%m.%Y"  # Время последней модификации
                    ),
                    isDir=False,
                ),
            )
