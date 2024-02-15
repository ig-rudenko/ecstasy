import pathlib
import string
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import IO

from check import models


@dataclass
class ConfigFile:
    """
    # Класс данных, представляющий файл конфигурации
    """

    name: str
    size: int
    modTime: str
    path: str | pathlib.Path = ""

    def __bool__(self):
        return bool(self.name)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Проверять на равенство можно только такой же тип класса: {self.__class__}, а не {other.__class__}"
            )
        return self.name == other.name and self.size == other.size and self.modTime == other.modTime


class ConfigStorage(ABC):
    """
    Абстрактный класс для представления хранилища конфигурационных файлов
    """

    @abstractmethod
    def __init__(self, device: models.Devices):
        self.device = device

    @abstractmethod
    def storage_path(self):
        pass

    @abstractmethod
    def check_storage(self) -> bool:
        """
        ## Проверяет, инициализирует или создает хранилище для оборудования.

        :return: OK?
        """
        pass

    @abstractmethod
    def open(self, file_name: str, mode: str = "rb", **kwargs) -> IO:
        """
        ## Открывает файл конфигурации

        :param file_name: Имя файла.
        :param mode: Режим доступа к файлу.
        :return: Объект `IO`.
        """
        pass

    @abstractmethod
    def delete(self, file_name: str) -> bool:
        """
        ## Удаляет файл конфигурации из хранилища

        :param file_name: Имя файла.
        :return: Удален?
        """
        pass

    @abstractmethod
    def files_list(self) -> list[ConfigFile]:
        """
        ## Возвращает список файлов конфигураций для оборудования

        :return: list[ConfigFile]
        """

        pass

    @abstractmethod
    def validate_config_name(self, file_name: str) -> bool:
        """
        ## Проверяет правильность имени файла конфигурации

        :param file_name: Имя файла.
        :return: OK?
        """
        pass

    @abstractmethod
    def is_exist(self, file_name: str) -> bool:
        """
        ## Проверяет наличие указанного файла конфигурации

        :param file_name: Имя файла.
        :return: Exist?
        """
        pass

    @abstractmethod
    def add(self, new_file_name: str, file_content=None, file_path: pathlib.Path | None = None):
        """
        ## Добавляет новый файл конфигурации

        Необходимо указать названия файла, а также:

        - Содержимое файла (str или bytes)
        либо

        - Путь к имеющемуся файлу конфигурации для его последующего сохранения в хранилище


        :param new_file_name: Название файла в хранилище.
        :param file_content: Содержимое файла (optional).
        :param file_path: Путь к файлу (optional).
        """
        pass

    @staticmethod
    def slug_name(device_name: str) -> str:
        """
        Очищаем название оборудования от лишних символов

        Также переводит русские символы в английские. Заменяет пробелы на "_".
        Удаляет другие пробельные символы "\\t \\n \\r \\f \\v"

        Максимальная длина строки 220

        :param device_name: Название оборудования
        :return: Очищенное название
        """

        unicode_ascii = {
            "а": "a",
            "б": "b",
            "в": "v",
            "г": "g",
            "д": "d",
            "е": "e",
            "ё": "e",
            "ж": "zh",
            "з": "z",
            "и": "i",
            "й": "i",
            "к": "k",
            "л": "l",
            "м": "m",
            "н": "n",
            "о": "o",
            "п": "p",
            "р": "r",
            "с": "s",
            "т": "t",
            "у": "u",
            "ф": "f",
            "х": "h",
            "ц": "c",
            "ч": "cz",
            "ш": "sh",
            "щ": "scz",
            "ъ": "",
            "ы": "y",
            "ь": "",
            "э": "e",
            "ю": "u",
            "я": "ja",
            "А": "A",
            "Б": "B",
            "В": "V",
            "Г": "G",
            "Д": "D",
            "Е": "E",
            "Ё": "E",
            "Ж": "ZH",
            "З": "Z",
            "И": "I",
            "Й": "I",
            "К": "K",
            "Л": "L",
            "М": "M",
            "Н": "N",
            "О": "O",
            "П": "P",
            "Р": "R",
            "С": "S",
            "Т": "T",
            "У": "U",
            "Ф": "F",
            "Х": "H",
            "Ц": "C",
            "Ч": "CZ",
            "Ш": "SH",
            "Щ": "SCH",
            "Ъ": "",
            "Ы": "y",
            "Ь": "",
            "Э": "E",
            "Ю": "U",
            "Я": "YA",
            " ": "_",
            "'": "/",
            "\\": "/",
            "[": "(",
            "]": ")",
            "{": "(",
            "}": ")",
            "—": "-",
        }

        ascii_str = ""
        for i in device_name:
            if i in unicode_ascii:
                ascii_str += unicode_ascii[i]
            elif i in string.whitespace:
                continue
            elif i.isascii():
                ascii_str += i

        return ascii_str
