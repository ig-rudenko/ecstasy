import logging
import os
import time
from queue import Empty, Queue
from threading import Thread
from typing import Any

from devicemanager import DeviceException, snmp
from devicemanager.dc import DeviceRemoteConnector
from devicemanager.device_connector.exceptions import MethodError
from devicemanager.session_control import DEVICE_SESSIONS
from devicemanager.vendors import BaseDevice

logger = logging.Logger(__file__)
logger.addHandler(logging.StreamHandler())

DEFAULT_POOL_SIZE = int(os.getenv("DEFAULT_POOL_SIZE", "3"))
MAX_POOL_SIZE = int(os.getenv("MAX_POOL_SIZE", "3"))


class DeviceSessionFactory:
    def __init__(
        self,
        ip: str,
        protocol: str,
        auth_obj,
        make_session_global: bool,
        pool_size: int | None,
        snmp_community: str,
        port_scan_protocol: str,
    ):
        self.port_scan_protocol = port_scan_protocol
        self.snmp_community = snmp_community
        self.pool_size = self._validate_pool_size(pool_size)

        self.make_session_global = make_session_global
        self.auth_obj = auth_obj
        self.protocol = protocol
        self.ip = ip
        self.connections: list[BaseDevice] = []

    @staticmethod
    def _validate_pool_size(pool_size) -> int:
        try:
            pool_size = int(pool_size)
        except (TypeError, ValueError):
            pool_size = DEFAULT_POOL_SIZE
        if pool_size < 1:
            return 1
        if pool_size > MAX_POOL_SIZE:
            return MAX_POOL_SIZE
        return pool_size

    def perform_method(self, method: str, **params) -> Any:
        if logger.level <= logging.DEBUG:
            logger.debug('Device: %s | Начало выполнение метода "%s", params=%s', self.ip, method, params)
            start_time = time.perf_counter()
            result = self._perform(method, **params)
            logger.debug(
                'Device: %s | Метод "%s" выполнялся %s сек, params=%s',
                self.ip,
                method,
                round(time.perf_counter() - start_time, 4),
                params,
            )
            return result

        return self._perform(method, **params)

    def _perform(self, method: str, **params) -> Any:
        if method == "get_interfaces" and self.port_scan_protocol == "snmp":
            # Получаем данные по SNMP
            return snmp.get_interfaces(device_ip=self.ip, community=self.snmp_community)

        device_connection = self._get_connection_to_perform()

        logger.debug(
            "Device: %s | Method=%s DeviceVendor=%s", self.ip, method, device_connection.__class__.__name__
        )

        if not hasattr(device_connection, method):
            raise MethodError

        session_method = getattr(device_connection, method)

        try:
            data = session_method(**params)
        except Exception as exc:
            device_connection.session.close()
            raise exc

        logger.debug(
            "Device: %s | Method=%s DeviceVendor=%s",
            self.ip,
            method,
            device_connection.__class__.__name__,
        )
        return data

    def _get_connection_to_perform(self) -> BaseDevice:
        if self.make_session_global:
            return self._make_and_get_connection()

        return DeviceRemoteConnector(
            ip=self.ip,
            protocol=self.protocol,
            auth_obj=self.auth_obj,
            snmp_community=self.snmp_community,
        ).get_session()

    def _make_and_get_connection(self) -> BaseDevice:
        start_time = time.perf_counter()

        if DEVICE_SESSIONS.has_pool(device_ip=self.ip):
            # Проверяем, что имеется пул, а если он еще создается, то необходимо подождать.
            # Иначе будет множественное создание пулов.
            # Ожидаем 30 сек.
            while not DEVICE_SESSIONS.pool_is_created(self.ip) and time.perf_counter() - start_time < 30.0:
                time.sleep(0.1)
            if time.perf_counter() - start_time > 30.0:
                # Если не удалось дождаться пула более 30с, очищаем его и будем создавать заново
                logger.debug("Device: %s | CLEAR POOL", self.ip)
                DEVICE_SESSIONS.clear_pool(self.ip)

        if DEVICE_SESSIONS.has_connection(self.ip):
            Thread(target=self._expand_to_pool_size, daemon=True).start()
            return DEVICE_SESSIONS.get_connection(self.ip)

        threads = []
        connections_queue: Queue = Queue(maxsize=self.pool_size)
        DEVICE_SESSIONS.get_or_create_pool(self.ip, self.pool_size)

        for i in range(self.pool_size):
            new_thread = Thread(
                target=self._add_device_session,
                args=(connections_queue,),
                name=f"Device: {self.ip} | Get session - {i}",
                daemon=True,
            )
            threads.append(new_thread)
            new_thread.start()

        first_connection = self.get_first_valid_connection(connections_queue)
        logger.debug("Device: %s | GOT FIRST CONNECTION: %s", self.ip, first_connection)
        # Сохраняем, если было указано хранение глобально.
        # Но для начала очистим пул от возможных не сброшенных подключений.
        DEVICE_SESSIONS.clear_pool(self.ip)
        DEVICE_SESSIONS.add_connections_to_pool(
            self.ip, pool_size=self.pool_size, connections=[first_connection]
        )
        Thread(
            target=self.add_to_pool_all_connections,
            args=(connections_queue,),
            name=f"Device: {self.ip} | Add to pool all connections - POOL_SIZE={self.pool_size}",
            daemon=True,
        ).start()

        return first_connection

    def _add_device_session(self, queue: Queue) -> None:
        try:
            logger.debug("Device: %s | Создаем сессию", self.ip)
            connection = DeviceRemoteConnector(
                ip=self.ip,
                protocol=self.protocol,
                auth_obj=self.auth_obj,
                snmp_community=self.snmp_community,
            ).get_session()

        except Exception as exc:
            logger.error("Device: %s | Ошибка при создании сессии", self.ip, exc_info=exc)
            queue.put(exc, block=True)

        else:
            logger.debug("Device: %s | Успешно создали сессию для", self.ip)
            queue.put(connection, block=True)

    @staticmethod
    def get_first_valid_connection(queue: Queue) -> BaseDevice:
        connection: Exception | BaseDevice | None = None
        while True:
            try:
                connection = queue.get(timeout=30)
            except Empty:
                break

            if connection is not None and not isinstance(connection, Exception):
                return connection
            if isinstance(connection, Exception):
                raise connection

        if isinstance(connection, Exception):
            raise connection
        if connection is None:
            raise DeviceException("Connection was not established")
        return connection

    def add_to_pool_all_connections(self, queue: Queue):
        while True:
            try:
                connection: Exception | BaseDevice = queue.get(timeout=30)
            except Empty:
                break

            if connection and not isinstance(connection, Exception):
                DEVICE_SESSIONS.add_connections_to_pool(
                    self.ip, pool_size=self.pool_size, connections=[connection]
                )
            logger.debug("Device: %s | Add session to pool - %s", self.ip, connection)

    def _expand_to_pool_size(self) -> None:
        logger.debug("Device: %s | Expand to pool size", self.ip)
        pool = DEVICE_SESSIONS.get_or_create_pool(self.ip, self.pool_size)
        length = self.pool_size - len(pool)

        if length <= 0:
            return

        queue: Queue = Queue(length)
        for i in range(length):
            Thread(
                target=self._add_device_session,
                args=(queue,),
                name=f"Device: {self.ip} | Get session - {i}",
                daemon=True,
            ).start()

        self.add_to_pool_all_connections(queue)
