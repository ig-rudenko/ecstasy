import ftplib
import pathlib
from dataclasses import dataclass
from re import Pattern

from .base import AbstractFTPCollector
from .exceptions import FileDownloadError, NotFound


@dataclass
class FTPItem:
    name: str
    mode: str

    def is_valid_item(self) -> bool:
        return self.name not in [".", ".."]

    def is_valid_dir(self) -> bool:
        return self.mode.startswith("d") and self.is_valid_item()

    def is_valid_file(self) -> bool:
        return self.mode.startswith("d") and self.is_valid_item()


class FTPCollector(AbstractFTPCollector):
    def __init__(self, host: str, timeout: int | None = None):
        self._ftp = ftplib.FTP(host, timeout=float(timeout or 0))
        self.local_dir: pathlib.Path = pathlib.Path()
        self.retry_after_fail = False
        self.retry_counts = 1

    def login(self, username: str, password: str, *args, **kwargs):
        self._ftp.login(username, password)

    def download_file(self, file_or_pattern: str | Pattern, local_dir: str, *args, **kwargs):
        pass

    def download_folder(
        self,
        folder_or_pattern: str | Pattern,
        local_dir: str | pathlib.Path,
        retry_after_fail: bool = False,
        retry_counts: int = 1,
    ) -> pathlib.Path:
        """
        Функция загружает файлы с FTP-сервера в локальный каталог либо путем указания пути к папке, либо с помощью
        шаблона регулярного выражения, соответствующего имени папки.

        :param folder_or_pattern: Этот параметр может быть либо строкой, либо шаблоном регулярного выражения. Он
         представляет собой имя папки или шаблон для сопоставления с именем папки на FTP-сервере.
        :param local_dir: Локальный каталог, в котором будет сохранена загруженная папка.
        :param retry_after_fail: Логический параметр, определяющий, следует ли повторять загрузку файла
         после неудачной попытки. Если установлено значение True, функция загрузки попытается снова загрузить файл после
         сбоя. Если установлено значение False, функция не будет повторять попытку и вернет сообщение об ошибке,
         defaults to False
        :param retry_counts: Параметр `retry_counts` представляет собой необязательный целочисленный аргумент,
         указывающий количество попыток повторной загрузки файла в случае сбоя. Если для параметра `retry_after_fail`
         установлено значение `True`, процесс загрузки будет повторен `retry_counts` раз (defaults to 1).
        """

        if isinstance(local_dir, str):
            self.local_dir = pathlib.Path(local_dir)
        elif isinstance(local_dir, pathlib.Path):
            self.local_dir = local_dir
        else:
            ValueError(f"`local_dir должен быть `str` либо `pathlib.Path`, а был передан {type(local_dir)}")

        self.retry_after_fail = retry_after_fail
        self.retry_counts = retry_counts

        if isinstance(folder_or_pattern, str):
            self._mirror_ftp_dir(folder_or_pattern)

            return self.local_dir / folder_or_pattern

        elif isinstance(folder_or_pattern, Pattern):
            folder = self._find_folder(pattern=folder_or_pattern)
            self._mirror_ftp_dir(folder)
            return self.local_dir / folder

        else:
            raise ValueError(
                f"Неверный тип параметра `folder_or_pattern`, "
                f"требуется `str` или `Pattern`, а был передан {type(folder_or_pattern)}"
            )

    def _list_dir(self, path: str) -> list[FTPItem]:
        """
        Возвращает список элементов в каталоге на FTP-сервере, как список объектов FTPItem, содержащих имя и режим
        каждого элемента.

        :param path: Параметр `path` представляет собой строку, представляющую путь к каталогу, содержимое которого мы
         хотим вывести.
        :return: список объектов FTPItem, которые представляют файлы и каталоги по указанному пути на FTP-сервере.
        """
        dir_list: list[FTPItem] = []
        self._ftp.retrlines(
            f"LIST {path}",
            callback=lambda x: dir_list.append(
                FTPItem(
                    name=x.split()[-1],
                    mode=x.split()[0],
                ),
            ),
        )
        return dir_list

    def _find_folder(self, pattern: Pattern) -> str:
        """
        Эта функция ищет папку, соответствующую заданному шаблону, в корневом каталоге и возвращает ее имя.

        :param pattern: Параметр `pattern` представляет собой шаблон регулярного выражения, который используется для
         сопоставления с именами элементов в каталоге. Метод _find_folder ищет папку в корневом каталоге ("/"),
         соответствующую шаблону, и возвращает имя первой найденной подходящей папки.
        :return: Если найдено имя папки, соответствующее заданному шаблону, то возвращается это имя папки. В противном
         случае возвращается пустая строка.
        """
        for item in self._list_dir("/"):
            if item.is_valid_item() and pattern.match(item.name):
                return item.name

        # Если не удалось найти папку по паттерну
        raise NotFound(f"По паттерну {repr(pattern.pattern)} не была найдена папка")

    def _mirror_ftp_dir(self, path: str):
        """
        Эта функция рекурсивно скачивает каталог с FTP-сервера в локальный каталог.

        :param path: Параметр path — это строка, представляющая путь к каталогу на FTP-сервере, который необходимо
         загрузить в локальный каталог.
        """
        for item in self._list_dir(path):
            print(item)
            if not item.is_valid_item():
                continue

            if item.is_valid_dir():
                self._mirror_ftp_dir(f"{path}/{item.name}")

            else:
                file_path = self.local_dir / path
                file_path.mkdir(parents=True, exist_ok=True)
                file_path = file_path / item.name

                self._ftp.cwd(path)

                # Цикл while с блоком try-except пытается загрузить файл с FTP-сервера и повторяет попытку,
                # если возникает ошибка socket.timeout. Количество повторных попыток определяется параметром
                # retry_counts. Если для `retry_after_fail` установлено значение `True`, функция попытается повторить
                # загрузку после сбоя. Если для `retry_after_fail` установлено значение `False`, функция вызовет
                # исключение после первого сбоя.
                file_retry_counts = self.retry_counts
                while file_retry_counts > 0:
                    try:
                        with file_path.open("wb") as f:
                            f.write(b"a")
                            self._ftp.retrbinary(f"RETR {item.name}", f.write)
                        break

                    except TimeoutError as exc:
                        if self.retry_after_fail:
                            file_retry_counts -= 1
                            continue

                        raise FileDownloadError(
                            f"Превышено время ожидания ({self._ftp.timeout} секунд) "
                            f"скачивания файла ({path}/{item.name})"
                        ) from exc

                self._ftp.cwd("/")
