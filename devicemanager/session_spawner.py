import logging
import os
import sys
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pexpect import spawn as Spawn  # noqa
else:
    from pexpect.spawnbase import SpawnBase as Spawn

if TYPE_CHECKING or sys.platform != "win32":
    from pexpect import spawn as Spawn  # noqa

logger = logging.getLogger(__name__)
logger.setLevel(str(os.getenv("DEVICE_CONNECTOR_LOG_LEVEL", "INFO")))
logger.addHandler(logging.StreamHandler(sys.stdout))


class SessionSpawner(Spawn):

    def __init__(
        self,
        command: str,
        ip: str,
        args: list[str] | None = None,
        timeout: float | None = 30,
        maxread: int = 2000,
        searchwindowsize: int | None = None,
        logfile=None,
        cwd=None,
        env: Mapping[str, str] | None = None,
        ignore_sighup: bool = False,
        echo: bool = True,
        preexec_fn: Callable[[], None] | None = None,
        encoding: str | None = None,
        codec_errors: str = "strict",
        dimensions: tuple[int, int] | None = None,
        use_poll: bool = False,
    ) -> None:
        if args is None:
            args = []

        super().__init__(
            command,
            args,
            timeout,
            maxread,
            searchwindowsize,
            logfile,
            cwd,
            env,
            ignore_sighup,
            echo,
            preexec_fn,
            encoding,
            codec_errors,
            dimensions,
            use_poll,
        )
        self.ip = ip

    def sendline(self, s: str | bytes = "") -> int:
        logger.debug("Device: %s | sendline: %s", self.ip, s)
        return super().sendline(s)

    def send(self, s: str | bytes) -> int:
        logger.debug("Device: %s | send: %s", self.ip, s)
        return super().send(s)

    def expect(
        self,
        pattern,
        timeout=-1,
        searchwindowsize=-1,
        async_=False,
    ):
        logger.debug("Device: %s | expect: %s", self.ip, pattern)

        res = super().expect(pattern, timeout, searchwindowsize, async_)  # noqa

        logger.debug("Device: %s | expect: %s", self.ip, res)
        logger.debug("Device: %s | before: %s", self.ip, self.before)
        return res
