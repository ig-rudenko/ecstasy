import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TypedDict

from devicemanager import DeviceException
from devicemanager.vendors import BaseDevice

logger = logging.Logger(__file__)


class PoolConnectionStatus(TypedDict):
    """Status and protocol of one device connection."""

    active: bool
    protocol: str


@dataclass
class GlobalSession:
    connection: BaseDevice

    @property
    def alive(self) -> bool:
        try:
            return self.connection.session.isalive()
        # pylint: disable-next=broad-exception-caught
        except Exception as exc:
            logger.error('Ошибка во время проверки статуса сессии "isalive"', exc_info=exc)
            return False

    def reserve(self, blocking: bool = True) -> bool:
        """Зарезервировать соединение для текущего потока."""

        return self.connection.acquire_session(blocking=blocking)

    def close(self) -> None:
        try:
            self.connection.session.close()
        # pylint: disable-next=broad-exception-caught
        except Exception as exc:
            logger.error("Ошибка во время удаления сессии", exc_info=exc)


class ConnectionPool:
    def __init__(self, max_size: int = 5):
        self._size = max_size
        self._pool: list[GlobalSession] = []
        self._created = False
        self._creation_error: Exception | None = None
        self._creation_event = threading.Event()
        self._expanding = False
        self._lock = threading.RLock()
        self.expired = datetime.now() + timedelta(minutes=2)

    def __bool__(self):
        with self._lock:
            return len(self._pool) > 0

    def __len__(self):
        with self._lock:
            return len(self._pool)

    @property
    def available(self) -> bool:
        with self._lock:
            return self.expired >= datetime.now()

    @property
    def is_created(self) -> bool:
        with self._lock:
            return self._created

    def set_created(self) -> None:
        """Пометить пул готовым и разбудить ожидающие потоки."""

        with self._lock:
            self._created = True
            self._creation_error = None
            self._creation_event.set()

    def set_creation_error(self, error: Exception) -> None:
        """Завершить создание пула ошибкой и разбудить ожидающие потоки."""

        with self._lock:
            self._creation_error = error
            self._creation_event.set()

    def wait_until_created(self, timeout: float) -> None:
        """Дождаться завершения создания пула или пробросить его ошибку."""

        if not self._creation_event.wait(timeout):
            raise TimeoutError("Timed out waiting for device session pool")

        with self._lock:
            if self._creation_error is not None:
                raise self._creation_error

    def reserve_expansion(self) -> int:
        """Зарезервировать недостающие слоты для одного фонового расширения."""

        with self._lock:
            if self._expanding:
                return 0

            self._pool = [connection for connection in self._pool if connection.alive]
            missing_connections = self._size - len(self._pool)
            if missing_connections > 0:
                self._expanding = True
            return missing_connections

    def finish_expansion(self) -> None:
        """Разрешить следующий запуск фонового расширения пула."""

        with self._lock:
            self._expanding = False

    def add(self, connection: GlobalSession) -> bool:
        """Добавить сессию, если в пуле остался свободный слот."""

        with self._lock:
            if len(self._pool) < self._size:
                self._pool.append(connection)
                return True

        return False

    def get(self) -> GlobalSession | None:
        with self._lock:
            if self.expired < datetime.now():
                return None

            last_available = None
            for conn in self._pool:
                if conn.alive:
                    last_available = conn
                    if conn.reserve(blocking=False):
                        return conn

        if last_available is not None:
            last_available.reserve()
        return last_available

    def renew(self) -> None:
        """Продлить срок жизни пула после использования."""

        with self._lock:
            self.expired = datetime.now() + timedelta(minutes=2)

    def close_all(self) -> None:
        with self._lock:
            connections = self._pool
            self._pool = []

        for conn in connections:
            conn.close()

    def clean_unavailable(self) -> None:
        with self._lock:
            active_pool = []
            for conn in self._pool:
                if conn.alive:
                    active_pool.append(conn)
            self._pool = active_pool

    def __iter__(self):
        with self._lock:
            return iter(tuple(self._pool))


class SessionController:
    def __init__(self) -> None:
        self._sessions: dict[str, ConnectionPool] = {}
        self._lock = threading.RLock()
        self.__cleaner_running = False

    def has_pool(self, device_ip: str) -> bool:
        with self._lock:
            return device_ip in self._sessions

    def get_or_create_pool(self, device_ip: str, pool_size: int) -> ConnectionPool:
        with self._lock:
            pool = self._sessions.get(device_ip)
            if pool is None:
                pool = ConnectionPool(max_size=pool_size)
                self._sessions[device_ip] = pool
            return pool

    def start_pool_creation(self, device_ip: str, pool_size: int) -> tuple[ConnectionPool, bool]:
        """Вернуть пул и указать, должен ли вызывающий поток создать его."""

        with self._lock:
            pool = self._sessions.get(device_ip)
            if pool is not None:
                return pool, False

            pool = ConnectionPool(max_size=pool_size)
            self._sessions[device_ip] = pool
            return pool, True

    def delete_pool(self, device_ip: str) -> None:
        with self._lock:
            pool = self._sessions.pop(device_ip, None)

        if pool is not None:
            pool.set_creation_error(DeviceException("Device session pool was deleted"))
            pool.close_all()

    def fail_pool(self, device_ip: str, pool: ConnectionPool, error: Exception) -> None:
        """Удалить конкретное поколение пула и сообщить ожидающим об ошибке."""

        pool.set_creation_error(error)
        with self._lock:
            if self._sessions.get(device_ip) is pool:
                del self._sessions[device_ip]
        pool.close_all()

    def remove_pool(self, device_ip: str, pool: ConnectionPool) -> bool:
        """Удалить пул, только если он всё ещё является текущим для устройства."""

        with self._lock:
            if self._sessions.get(device_ip) is not pool:
                return False
            del self._sessions[device_ip]

        pool.close_all()
        return True

    def pool_is_created(self, device_ip: str) -> bool:
        with self._lock:
            pool = self._sessions.get(device_ip)
        if pool is not None:
            return pool.is_created
        return False

    def clear_pool(self, device_ip: str) -> None:
        with self._lock:
            pool = self._sessions.get(device_ip)
        if pool is not None:
            pool.close_all()

    def add_connections_to_pool(
        self,
        device_ip: str,
        pool_size: int,
        connections: list[BaseDevice],
        expected_pool: ConnectionPool | None = None,
    ) -> bool:
        """Добавить сессии только в актуальное поколение пула."""

        rejected_connections = []
        with self._lock:
            pool = self._sessions.get(device_ip)
            if pool is None and expected_pool is None:
                pool = ConnectionPool(max_size=pool_size)
                self._sessions[device_ip] = pool

            if pool is None or (expected_pool is not None and pool is not expected_pool):
                rejected_connections = connections
                pool_is_current = False
            else:
                pool_is_current = True
                for conn in connections:
                    global_session = GlobalSession(connection=conn)
                    if not pool.add(global_session):
                        rejected_connections.append(conn)

                pool.set_created()

        for connection in rejected_connections:
            GlobalSession(connection=connection).close()
        return pool_is_current

    def has_connection(self, device_ip) -> bool:
        with self._lock:
            conn_pool = self._sessions.get(device_ip)
        if conn_pool is not None:
            return conn_pool.available and any(conn.alive for conn in conn_pool)
        return False

    def get_connection(self, device_ip) -> BaseDevice:
        with self._lock:
            pool = self._sessions.get(device_ip)
        if pool is None:
            raise DeviceException("Device session pool not found")
        # Продлеваем срок действия сессий еще на 2 минуты.
        pool.renew()
        session = pool.get()
        if session is None:
            raise DeviceException("Device session not found")
        return session.connection

    def session_cleaner(self) -> None:
        """
        Эта функция удаляет все сеансы старше текущего времени за вычетом переменной session_timeout.
        """
        while self.__cleaner_running:
            with self._lock:
                session_pools = tuple(self._sessions.items())

            for ip, pool in session_pools:
                pool.clean_unavailable()
                if not pool.available:
                    self.remove_pool(ip, pool)

            time.sleep(30)

    def run_session_cleaner(self) -> None:
        self.__cleaner_running = True
        threading.Thread(
            target=SessionController.session_cleaner,
            args=(self,),
            daemon=True,
            name="Devices connections cleaner",
        ).start()

    def get_pool_status(self, ip: str) -> list[bool]:
        """Return compatibility list containing only connection activity."""

        return [connection["active"] for connection in self.get_pool_connections(ip)]

    def get_pool_connections(self, ip: str) -> list[PoolConnectionStatus]:
        """Return activity and actual protocol for every pooled connection."""

        with self._lock:
            pool = self._sessions.get(ip)
        if pool is None:
            return []

        connections: list[PoolConnectionStatus] = []
        for conn in pool:  # type: GlobalSession
            connections.append(
                {
                    "active": conn.alive,
                    "protocol": getattr(conn.connection, "connection_protocol", ""),
                }
            )
        return connections


DEVICE_SESSIONS = SessionController()
DEVICE_SESSIONS.run_session_cleaner()
