import hashlib
import pathlib
import re
import shutil
from typing import Union

from gathering.ftp.exceptions import FTPCollectorError
from .base import ConfigStorage
from .exceptions import ConfigFileError


class ConfigurationGather:
    def __init__(self, storage: ConfigStorage):

        self.storage = storage
        self.files = self.storage.files_list()

        self.last_config_file = self.files[0] if self.files else None
        self.re_pattern_space = re.compile(r"\s")

    def delete_outdated_configs(self):
        """
        ##  Удаляет файлы, если их больше 10
        """
        # Удаление файлов в каталоге, кроме 10 самых последних.
        for file in self.files[:-10]:
            self.storage.delete(file.name)

    def _save_by_content(self, current_config: Union[str, bytes], file_format: str) -> bool:
        """
        ## Берет текущую конфигурацию, удаляет все пробелы, хеширует ее и сравниваем с последней конфигурацией.
        Если они совпадают, то возвращает False.
        Если они разные, то сохраняет текущую конфигурацию в хранилище и возвращает True.

        :param current_config: [str, bytes] - текущая конфигурация устройства
        :param file_format: Формат файла `.txt`, `.zip`, или пустая строка
        :return: Правда или ложь.
        """

        # Сохраняем в исходном виде конфигурацию
        unformatted_config = current_config

        read_mode = "rb"
        last_config: bytes = b""

        if isinstance(current_config, str):
            read_mode = "r"
            current_config: bytes = self.re_pattern_space.sub("", current_config).encode()

        if self.last_config_file:
            try:
                # Открытие файла в режиме чтения.
                with self.storage.open(self.last_config_file.name, mode=read_mode) as file:
                    # Чтение последнего файла конфигурации.
                    last_config = file.read()
            # Резервный вариант, когда файл не в формате ascii или отсутствует.
            except (UnicodeError, FileNotFoundError):
                last_config: str = ""

        if isinstance(last_config, str):
            last_config: bytes = self.re_pattern_space.sub("", last_config).encode()

        # Берем текущую конфигурацию и удаляем все пробелы, а затем хешируем ее.
        current_config_hash = hashlib.sha3_224(current_config).hexdigest()

        # Берем прошлую конфигурацию и удаляем все пробелы, а затем хешируем ее.
        last_config_hash = hashlib.sha3_224(last_config).hexdigest()

        # Проверяем, совпадает ли last_config с current_config.
        if last_config_hash == current_config_hash:
            return False

        # Создание нового имени файла для нового файла конфигурации.
        new_file_name = f"config_file_{self.storage.device.name}___{self.storage.device.ip}{file_format}"

        self.storage.add(new_file_name=new_file_name, file_content=unformatted_config)

        return True

    def save_config(self, new_config: Union[str, pathlib.Path]) -> bool:
        """
        Сохраняем конфигурацию в зависимости от типа (str или pathlib.Path)
        """

        # Если файл представлен в виде строки
        if isinstance(new_config, str):
            return self._save_by_content(current_config=new_config, file_format=".txt")

        file_format = ""  # По умолчанию без формата

        # Если конфигурация представлена в виде папки, то делаем из неё архив и удаляем всю папку
        if isinstance(new_config, pathlib.Path) and new_config.is_dir():
            shutil.make_archive(new_config, "zip", new_config)  # Создаем архив
            new_config_folder = new_config
            # Меняем путь на созданный архив
            new_config = new_config.parent / f"{new_config.name}.zip"
            shutil.rmtree(new_config_folder, ignore_errors=True)  # Удаляем папку

            file_format = ".zip"

        # Если файл был скачан, то используем его путь
        if isinstance(new_config, pathlib.Path) and new_config.is_file():

            # Записываем содержимое скачанного файла
            with new_config.open("rb") as f:
                file_data = f.read()
            # Удаляем его, так как далее будет сохранен новый файл в хранилище
            new_config.unlink()

            # Обрабатываем содержимое файла
            return self._save_by_content(current_config=file_data, file_format=file_format)

        return False

    def collect_config_file(self) -> bool:
        """
        Подключаемся к оборудованию и вызываем метод для получения текущей конфигурации
        """

        with self.storage.device.connect(make_session_global=False) as session:
            if hasattr(session, "get_current_configuration"):
                try:
                    current_config = session.get_current_configuration(
                        local_folder_path=self.storage.storage_path()
                    )
                    return self.save_config(current_config)
                except FTPCollectorError as error:
                    raise ConfigFileError(error.message) from error
            else:
                raise ConfigFileError(
                    f"Данное оборудование не поддерживает сохранение конфигурации"
                )
