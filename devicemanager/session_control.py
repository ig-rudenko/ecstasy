import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List

from devicemanager.vendors import BaseDevice


@dataclass
class GlobalSession:
    connection: BaseDevice
    expired: datetime

    @property
    def alive(self):
        return self.connection and self.connection.session and self.connection.session.isalive()

    @property
    def available(self):
        return self.expired >= datetime.now()

    @property
    def non_locked(self):
        return not self.connection.lock


class ConnectionPool:
    def __init__(self, max_size: int = 5):
        self._size = max_size
        self._pool: List[GlobalSession] = []
        self._created = False

    def __bool__(self):
        return len(self._pool) > 0

    @property
    def is_created(self):
        return self._created

    def set_created(self):
        self._created = True

    def add(self, connection: GlobalSession):
        if len(self._pool) < self._size:
            self._pool.append(connection)

    def get(self) -> GlobalSession:
        last_available = None
        for conn in self._pool:
            if conn.available and conn.alive:
                last_available = conn
                if conn.non_locked:
                    return conn
        return last_available

    def cleanup(self):
        for conn in self._pool:
            if not conn.available and conn.alive:
                conn.connection.session.close()
                self._pool.remove(conn)
            elif not conn.available and not conn.alive:
                self._pool.remove(conn)

    def close_all(self):
        for conn in self._pool:
            if conn.alive:
                conn.connection.session.close()
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

    def add_pool(self, device_ip: str, pool_size: int):
        if not self._sessions.get(device_ip):
            self._sessions[device_ip] = ConnectionPool(max_size=pool_size)

    def pool_is_created(self, device_ip: str) -> bool:
        pool = self._sessions.get(device_ip, None)
        if pool:
            return pool.is_created
        return False

    def clear_pool(self, device_ip: str):
        pool = self._sessions.get(device_ip)
        if pool:
            pool.close_all()

    def add_connections_to_pool(self, device_ip: str, connection: List[BaseDevice]):
        pool = self._sessions[device_ip]
        for conn in connection:
            pool.add(
                GlobalSession(
                    connection=conn,
                    expired=datetime.now() + timedelta(minutes=2),
                )
            )
        pool.set_created()

    def has_connection(self, device_ip) -> bool:
        conn_pool = self._sessions.get(device_ip, [])
        return any(conn.alive and conn.available for conn in conn_pool)

    def get_connection(self, device_ip) -> BaseDevice:
        pool = self._sessions.get(device_ip)
        session = pool.get()
        # Продлеваем срок действия сессии еще на 2 минуты.
        session.expired = datetime.now() + timedelta(minutes=2)
        return session.connection

    def session_cleaner(self):
        """
        Эта функция удаляет все сеансы старше текущего времени за вычетом переменной session_timeout.
        """
        while self.__cleaner_running:
            for ip, pool in tuple(self._sessions.items()):
                pool.cleanup()
                if not pool:
                    del self._sessions[ip]

            time.sleep(30)

    def run_session_cleaner(self):
        self.__cleaner_running = True
        threading.Thread(
            target=SessionController.session_cleaner,
            args=(self,),
            daemon=True,
            name="Session Cleaner",
        ).start()


DEVICE_SESSIONS = SessionController()
DEVICE_SESSIONS.run_session_cleaner()
