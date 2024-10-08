import hashlib
import re

from devicemanager.remote.exceptions import InvalidMethod
from gathering.services.ftp.exceptions import FTPCollectorError
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

    def _save_by_content(self, current_config: str | bytes, file_format: str) -> bool:
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
        last_config_bytes: bytes = b""

        if isinstance(current_config, str):
            read_mode = "r"
            current_config_bytes: bytes = self.re_pattern_space.sub("", current_config).encode()
        else:
            current_config_bytes = current_config

        if self.last_config_file and read_mode == "r":
            try:
                # Открытие файла в режиме чтения.
                with self.storage.open(self.last_config_file.name, mode=read_mode) as file:
                    # Чтение последнего файла конфигурации.
                    last_config_text: str = file.read()
                last_config_bytes = self.re_pattern_space.sub("", last_config_text).encode()

            # Резервный вариант, когда файл не в формате ascii или отсутствует.
            except (UnicodeError, FileNotFoundError):
                pass

        # Берем текущую конфигурацию и удаляем все пробелы, а затем хешируем ее.
        current_config_hash = hashlib.sha3_224(current_config_bytes).hexdigest()

        # Берем прошлую конфигурацию и удаляем все пробелы, а затем хешируем ее.
        last_config_hash = hashlib.sha3_224(last_config_bytes).hexdigest()

        # Проверяем, совпадает ли last_config с current_config.
        if last_config_hash == current_config_hash:
            return False

        # Создание нового имени файла для нового файла конфигурации.
        new_file_name = (
            f"{self.storage.device.name}___{self.storage.device.ip}___{current_config_hash[:10]}{file_format}"
        )

        self.storage.add(new_file_name=new_file_name, file_content=unformatted_config)

        return True

    def save_config(self, new_config: str | bytes, file_name: str) -> bool:
        """
        Сохраняем конфигурацию в зависимости от типа (str или bytes)
        """

        file_split = file_name.split(".")
        file_format = ""
        if len(file_split) > 1:
            file_format = f".{file_split[-1]}"

        if isinstance(new_config, str):
            return self._save_by_content(current_config=new_config, file_format=file_format or ".txt")
        elif isinstance(new_config, bytes):
            return self._save_by_content(current_config=new_config, file_format=file_format or "")

        return False

    def collect_config_file(self) -> bool:
        """
        Подключаемся к оборудованию и вызываем метод для получения текущей конфигурации
        """

        session = self.storage.device.connect(make_session_global=False)
        try:
            current_config_data, file_name = session.get_current_configuration()
            return self.save_config(current_config_data, file_name)
        except FTPCollectorError as error:
            raise ConfigFileError(error.message) from error
        except InvalidMethod:
            raise ConfigFileError("Данное оборудование не поддерживает сохранение конфигурации")
