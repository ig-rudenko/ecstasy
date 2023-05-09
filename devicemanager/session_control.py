import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict

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


class SessionController:
    def __init__(self):
        self._sessions: Dict[str, GlobalSession] = {}
        self.__cleaner_running = False

    def add_connection(self, device_ip: str, connection: BaseDevice):
        self._sessions[device_ip] = GlobalSession(
            connection=connection,
            expired=datetime.now() + timedelta(minutes=2),
        )

    def has_connection(self, device_ip) -> bool:
        connection = self._sessions.get(device_ip, False)
        return connection and connection.alive and connection.available

    def get_connection(self, device_ip) -> BaseDevice:
        session = self._sessions.get(device_ip)
        # Продлеваем срок действия сессии еще на 2 минуты.
        session.expired = datetime.now() + timedelta(minutes=2)
        return session.connection

    def session_cleaner(self):
        """
        Эта функция удаляет все сеансы старше текущего времени за вычетом переменной session_timeout.
        """
        while self.__cleaner_running:
            for ip, session in tuple(self._sessions.items()):
                if not session.available and session.alive:
                    session.connection.session.close()
                    del self._sessions[ip]
                elif not session.available and not session.alive:
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
