import pathlib
from abc import ABC, abstractmethod
from typing import Union, Pattern


class AbstractFTPCollector(ABC):
    @abstractmethod
    def login(self, username: str, password: str, *args, **kwargs):
        pass

    @abstractmethod
    def download_folder(
        self, folder_or_pattern: Union[str, Pattern], local_dir: str, *args, **kwargs
    ) -> pathlib.Path:
        pass

    @abstractmethod
    def download_file(self, file_or_pattern: Union[str, Pattern], local_dir: str, *args, **kwargs):
        pass
