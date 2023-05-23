class FTPCollectorError(Exception):
    def __init__(self, message: str):
        self.message = message


class FileDownloadError(FTPCollectorError):
    pass


class NotFound(FTPCollectorError):
    pass
