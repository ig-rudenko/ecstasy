import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from devicemanager.vendors import BaseDevice

logger = logging.Logger(__file__)


@dataclass
class GlobalSession:
    connection: BaseDevice

    @property
    def alive(self) -> bool:
        try:
            return self.connection.session.isalive()
        except Exception as exc:
            logger.error('Ошибка во время проверки статуса сессии "isalive"', exc_info=exc)
            return False

    @property
    def non_locked(self) -> bool:
        return not self.connection.lock

    def close(self) -> None:
        try:
            self.connection.session.close()
        except Exception as exc:
            logger.error("Ошибка во время удаления сессии", exc_info=exc)


class ConnectionPool:
    def __init__(self, max_size: int = 5):
        self._size = max_size
        self._pool: List[GlobalSession] = []
        self._created = False
        self.expired = datetime.now() + timedelta(minutes=2)

    def __bool__(self):
        return len(self._pool) > 0

    def __len__(self):
        return len(self._pool)

    @property
    def available(self) -> bool:
        return self.expired >= datetime.now()

    @property
    def is_created(self) -> bool:
        return self._created

    def set_created(self) -> None:
        self._created = True

    def add(self, connection: GlobalSession) -> None:
        if len(self._pool) < self._size:
            self._pool.append(connection)
        else:
            connection.connection.session.close()

    def get(self) -> Optional[GlobalSession]:
        if not self.available:
            return None

        last_available = None
        for conn in self._pool:
            if conn.alive:
                last_available = conn
                if conn.non_locked:
                    return conn
        return last_available

    def close_all(self) -> None:
        for conn in self._pool:
            conn.close()
        self._pool = []

    def __iter__(self):
        return iter(self._pool)


class SessionController:
    def __init__(self):
        self._sessions: Dict[str, ConnectionPool] = {}
        self.__cleaner_running = False

    def has_pool(self, device_ip: str) -> bool:
        pool = self._sessions.get(device_ip, None)
        return pool is not None

    def get_or_create_pool(self, device_ip: str, pool_size: int) -> ConnectionPool:
        if not self._sessions.get(device_ip):
            self._sessions[device_ip] = ConnectionPool(max_size=pool_size)
        return self._sessions[device_ip]

    def delete_pool(self, device_ip: str) -> None:
        self.clear_pool(device_ip)
        if self._sessions.get(device_ip, None) is not None:
            del self._sessions[device_ip]

    def pool_is_created(self, device_ip: str) -> bool:
        pool = self._sessions.get(device_ip, None)
        if pool is not None:
            return pool.is_created
        return False

    def clear_pool(self, device_ip: str) -> None:
        pool = self._sessions.get(device_ip)
        if pool:
            pool.close_all()

    def add_connections_to_pool(
        self, device_ip: str, pool_size: int, connections: List[BaseDevice]
    ) -> None:
        pool = self.get_or_create_pool(device_ip, pool_size)

        for conn in connections:
            pool.add(GlobalSession(connection=conn))

        pool.set_created()

    def has_connection(self, device_ip) -> bool:
        conn_pool = self._sessions.get(device_ip)
        if conn_pool is not None:
            return conn_pool.available and any(conn.alive for conn in conn_pool)
        return False

    def get_connection(self, device_ip) -> BaseDevice:
        pool = self._sessions.get(device_ip)
        # Продлеваем срок действия сессий еще на 2 минуты.
        pool.expired = datetime.now() + timedelta(minutes=2)
        session = pool.get()
        return session.connection

    def session_cleaner(self) -> None:
        """
        Эта функция удаляет все сеансы старше текущего времени за вычетом переменной session_timeout.
        """
        while self.__cleaner_running:
            for ip, pool in tuple(self._sessions.items()):
                if not pool.available:
                    pool.close_all()
                    del self._sessions[ip]

            time.sleep(30)

    def run_session_cleaner(self) -> None:
        self.__cleaner_running = True
        threading.Thread(
            target=SessionController.session_cleaner,
            args=(self,),
            daemon=True,
            name="Devices connections cleaner",
        ).start()


DEVICE_SESSIONS = SessionController()
DEVICE_SESSIONS.run_session_cleaner()
