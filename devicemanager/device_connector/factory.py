import logging
import os
import time
from queue import Empty, Queue
from threading import Event, Lock, Thread
from typing import Any

from devicemanager import DeviceException, snmp
from devicemanager.connection_ports import normalize_connection_ports
from devicemanager.dc import DeviceRemoteConnector
from devicemanager.device_connector.exceptions import MethodError
from devicemanager.session_control import DEVICE_SESSIONS, ConnectionPool
from devicemanager.vendors import BaseDevice

logger = logging.Logger(__file__)
logger.addHandler(logging.StreamHandler())

DEFAULT_POOL_SIZE = int(os.getenv("DEFAULT_POOL_SIZE", "3"))
MAX_POOL_SIZE = int(os.getenv("MAX_POOL_SIZE", "3"))
SESSION_CREATION_TIMEOUT = 30.0


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
        telnet_port: int | None = None,
        ssh_port: int | None = None,
        snmp_port: int | None = None,
    ):
        ports = normalize_connection_ports(
            telnet_port=telnet_port,
            ssh_port=ssh_port,
            snmp_port=snmp_port,
        )
        self.port_scan_protocol = port_scan_protocol
        self.snmp_community = snmp_community
        self.telnet_port = ports.telnet_port
        self.ssh_port = ports.ssh_port
        self.snmp_port = ports.snmp_port
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
            return snmp.get_interfaces(
                device_ip=self.ip,
                community=self.snmp_community,
                snmp_port=self.snmp_port,
            )

        device_connection = self._get_connection_to_perform()

        logger.debug(
            "Device: %s | Method=%s DeviceVendor=%s", self.ip, method, device_connection.__class__.__name__
        )

        if not hasattr(device_connection, method):
            if not self.make_session_global:
                device_connection.session.close()
            raise MethodError

        session_method = getattr(device_connection, method)

        try:
            data = session_method(**params)
        except Exception:
            device_connection.session.close()
            raise

        if not self.make_session_global:
            device_connection.session.close()

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
            telnet_port=self.telnet_port,
            ssh_port=self.ssh_port,
            snmp_port=self.snmp_port,
        ).get_session()

    def _make_and_get_connection(self) -> BaseDevice:
        while True:
            pool, should_create = DEVICE_SESSIONS.start_pool_creation(self.ip, self.pool_size)
            if should_create:
                break

            try:
                pool.wait_until_created(SESSION_CREATION_TIMEOUT)
            except TimeoutError as exc:
                error = DeviceException("Timed out waiting for device session pool", ip=self.ip)
                DEVICE_SESSIONS.fail_pool(self.ip, pool, error)
                raise error from exc

            if DEVICE_SESSIONS.has_connection(self.ip):
                self._schedule_pool_expansion(pool)
                return DEVICE_SESSIONS.get_connection(self.ip)

            DEVICE_SESSIONS.remove_pool(self.ip, pool)

        connections_queue: Queue = Queue(maxsize=self.pool_size)
        creation_cancelled = Event()
        results_lock = Lock()

        for i in range(self.pool_size):
            new_thread = Thread(
                target=self._add_device_session,
                args=(connections_queue, creation_cancelled, results_lock),
                name=f"Device: {self.ip} | Get session - {i}",
                daemon=True,
            )
            new_thread.start()

        deadline = time.perf_counter() + SESSION_CREATION_TIMEOUT
        try:
            first_connection, consumed_results = self._wait_for_first_valid_connection(
                connections_queue,
                expected_results=self.pool_size,
                deadline=deadline,
            )
        except Exception as exc:
            self._cancel_session_creation(connections_queue, creation_cancelled, results_lock)
            DEVICE_SESSIONS.fail_pool(self.ip, pool, exc)
            raise

        remaining_results = self.pool_size - consumed_results
        if remaining_results > 0:
            pool.reserve_expansion()

        logger.debug("Device: %s | GOT FIRST CONNECTION: %s", self.ip, first_connection)
        connection_added = DEVICE_SESSIONS.add_connections_to_pool(
            self.ip,
            pool_size=self.pool_size,
            connections=[first_connection],
            expected_pool=pool,
        )
        if not connection_added:
            pool.finish_expansion()
            self._cancel_session_creation(connections_queue, creation_cancelled, results_lock)
            raise DeviceException("Device session pool was replaced during creation", ip=self.ip)

        if remaining_results > 0:
            Thread(
                target=self._collect_pool_connections,
                args=(
                    connections_queue,
                    remaining_results,
                    pool,
                    deadline,
                    creation_cancelled,
                    results_lock,
                ),
                name=f"Device: {self.ip} | Add to pool all connections - POOL_SIZE={self.pool_size}",
                daemon=True,
            ).start()

        return first_connection

    def _add_device_session(self, queue: Queue, cancelled: Event, results_lock: Lock) -> None:
        """Создать одну сессию и безопасно передать результат ожидающему потоку."""

        try:
            logger.debug("Device: %s | Создаем сессию", self.ip)
            connection = DeviceRemoteConnector(
                ip=self.ip,
                protocol=self.protocol,
                auth_obj=self.auth_obj,
                snmp_community=self.snmp_community,
                telnet_port=self.telnet_port,
                ssh_port=self.ssh_port,
                snmp_port=self.snmp_port,
            ).get_session()

        except Exception as exc:
            logger.error("Device: %s | Ошибка при создании сессии", self.ip, exc_info=exc)
            result: Exception | BaseDevice = exc

        else:
            logger.debug("Device: %s | Успешно создали сессию для", self.ip)
            result = connection

        with results_lock:
            if cancelled.is_set():
                if not isinstance(result, Exception):
                    result.session.close()
                return
            queue.put_nowait(result)

    @staticmethod
    def get_first_valid_connection(queue: Queue) -> BaseDevice:
        """Вернуть первую успешную сессию, не завершаясь на первой ошибке."""

        connection, _ = DeviceSessionFactory._wait_for_first_valid_connection(
            queue,
            expected_results=queue.maxsize or 1,
            deadline=time.perf_counter() + SESSION_CREATION_TIMEOUT,
        )
        return connection

    @staticmethod
    def _wait_for_first_valid_connection(
        queue: Queue,
        expected_results: int,
        deadline: float,
    ) -> tuple[BaseDevice, int]:
        """Дождаться первой успешной сессии в пределах общего дедлайна."""

        last_error: Exception | None = None
        for consumed_results in range(1, expected_results + 1):
            remaining_time = deadline - time.perf_counter()
            if remaining_time <= 0:
                break

            try:
                connection: Exception | BaseDevice = queue.get(timeout=remaining_time)
            except Empty:
                break

            if not isinstance(connection, Exception):
                return connection, consumed_results
            if isinstance(connection, Exception):
                last_error = connection

        if last_error is not None:
            raise last_error
        raise DeviceException("Connection was not established")

    @staticmethod
    def _cancel_session_creation(queue: Queue, cancelled: Event, results_lock: Lock) -> None:
        """Остановить публикацию результатов и закрыть уже созданные сессии."""

        with results_lock:
            cancelled.set()
            while True:
                try:
                    connection: Exception | BaseDevice = queue.get_nowait()
                except Empty:
                    break
                if not isinstance(connection, Exception):
                    connection.session.close()

    def add_to_pool_all_connections(
        self,
        queue: Queue,
        expected_results: int,
        pool: ConnectionPool,
        deadline: float,
        cancelled: Event,
        results_lock: Lock,
    ) -> None:
        """Собрать известное число оставшихся результатов без лишнего ожидания."""

        received_results = 0
        while received_results < expected_results:
            remaining_time = deadline - time.perf_counter()
            if remaining_time <= 0:
                break

            try:
                connection: Exception | BaseDevice = queue.get(timeout=remaining_time)
            except Empty:
                break

            received_results += 1

            if connection and not isinstance(connection, Exception):
                DEVICE_SESSIONS.add_connections_to_pool(
                    self.ip,
                    pool_size=self.pool_size,
                    connections=[connection],
                    expected_pool=pool,
                )
            logger.debug("Device: %s | Add session to pool - %s", self.ip, connection)

        if received_results < expected_results:
            self._cancel_session_creation(queue, cancelled, results_lock)

    def _collect_pool_connections(
        self,
        queue: Queue,
        expected_results: int,
        pool: ConnectionPool,
        deadline: float,
        cancelled: Event,
        results_lock: Lock,
    ) -> None:
        """Заполнить пул оставшимися результатами и снять флаг расширения."""

        try:
            self.add_to_pool_all_connections(
                queue,
                expected_results,
                pool,
                deadline,
                cancelled,
                results_lock,
            )
        finally:
            pool.finish_expansion()

    def _schedule_pool_expansion(self, pool: ConnectionPool) -> None:
        """Запустить не более одного фонового расширения конкретного пула."""

        missing_connections = pool.reserve_expansion()
        if missing_connections <= 0:
            return

        Thread(
            target=self._expand_to_pool_size,
            args=(pool, missing_connections),
            name=f"Device: {self.ip} | Expand pool - {missing_connections}",
            daemon=True,
        ).start()

    def _expand_to_pool_size(self, pool: ConnectionPool, missing_connections: int) -> None:
        """Создать зарезервированное число недостающих сессий."""

        logger.debug("Device: %s | Expand to pool size", self.ip)
        queue: Queue = Queue(missing_connections)
        cancelled = Event()
        results_lock = Lock()
        deadline = time.perf_counter() + SESSION_CREATION_TIMEOUT

        for i in range(missing_connections):
            Thread(
                target=self._add_device_session,
                args=(queue, cancelled, results_lock),
                name=f"Device: {self.ip} | Get session - {i}",
                daemon=True,
            ).start()

        self._collect_pool_connections(
            queue,
            missing_connections,
            pool,
            deadline,
            cancelled,
            results_lock,
        )
