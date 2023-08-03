import logging
import time
from threading import Thread
from typing import List, Any

import pexpect

from devicemanager import snmp
from devicemanager.dc import DeviceFactory
from devicemanager.device_connector.exceptions import MethodError
from devicemanager.session_control import DEVICE_SESSIONS
from devicemanager.vendors import BaseDevice


logger = logging.Logger(__file__)


class DeviceSessionFactory:
    def __init__(
        self,
        ip: str,
        protocol: str,
        auth_obj,
        make_session_global: bool,
        pool_size: int,
        snmp_community: str,
        port_scan_protocol: str,
    ):
        self.port_scan_protocol = port_scan_protocol
        self.snmp_community = snmp_community
        self.pool_size = pool_size
        self.make_session_global = make_session_global
        self.auth_obj = auth_obj
        self.protocol = protocol
        self.ip = ip
        self.connections: List[BaseDevice] = []

    def perform_method(self, method: str, **params) -> Any:
        logger.debug(f'Начало выполнение метода "{method}", params={params}, ip={self.ip}')
        return self._perform(method, last_try=False, **params)

    def _perform(self, method: str, last_try: bool, **params) -> Any:
        device_connection = self._get_connection_to_perform()

        logger.info(f"{self.ip} {method}, {device_connection.__class__.__name__}")

        if method == "get_interfaces" and self.port_scan_protocol == "snmp":
            interfaces = snmp.get_interfaces(device_ip=self.ip, community=self.snmp_community)
            return interfaces

        if hasattr(device_connection, method):
            session_method = getattr(device_connection, method)

            try:
                method_data = session_method(**params)
            except (pexpect.TIMEOUT, pexpect.EOF) as exc:
                logger.error(
                    f"Ошибка {exc.__class__.__name__} при выполнении метода {method}, ip={self.ip}",
                    exc_info=exc,
                )
                if device_connection.session.isalive():
                    device_connection.session.close()

                if self.make_session_global:
                    # Пересоздаем сессию
                    logger.info(f"Пересоздаем сессию {self.ip}")
                    Thread(
                        target=self._create_and_append_new_connection,
                        args=(self,),
                        name=f"Create connection for {self.ip} - daemon",
                        daemon=True,
                    ).start()

                if not last_try:
                    # Пробуем в другой сессии пересоздать
                    self._perform(method, last_try=True, **params)
                else:
                    raise exc
            else:
                return method_data

            finally:
                if not self.make_session_global:
                    device_connection.session.close()

        else:
            raise MethodError()

    def _get_connection_to_perform(self) -> BaseDevice:
        if self.make_session_global:
            return self._make_and_get_connection()
        else:
            return DeviceFactory(
                ip=self.ip,
                protocol=self.protocol,
                auth_obj=self.auth_obj,
                snmp_community=self.snmp_community,
            ).get_session()

    def _create_and_append_new_connection(self) -> None:
        connections = []
        self._add_device_session(connections, append_exc=False)
        DEVICE_SESSIONS.add_connections_to_pool(
            self.ip, pool_size=self.pool_size, connections=connections
        )

    def _make_and_get_connection(self) -> BaseDevice:

        start_time = time.perf_counter()

        if DEVICE_SESSIONS.has_pool(device_ip=self.ip):
            # Проверяем, что имеется пул, а если он еще создается, то необходимо подождать.
            # Иначе будет множественное создание пулов.
            # Ожидаем 30 сек.
            while (
                not DEVICE_SESSIONS.pool_is_created(self.ip)
                and time.perf_counter() - start_time < 30.0
            ):
                time.sleep(0.3)
            if time.perf_counter() - start_time > 30.0:
                # Если не удалось дождаться пула более 30с, очищаем его и будем создавать заново
                logger.debug(f"CLEAR POOL {self.ip}")
                DEVICE_SESSIONS.clear_pool(self.ip)

        if DEVICE_SESSIONS.has_connection(self.ip):
            self._check_and_expand_to_pool_size()
            return DEVICE_SESSIONS.get_connection(self.ip)

        threads = []
        connections: List[BaseDevice] = []
        for i in range(self.pool_size):
            new_thread = Thread(
                target=self._add_device_session,
                args=(connections,),
                name=f"Get session for ip {self.ip} - {i}",
            )
            threads.append(new_thread)
            new_thread.start()

        for i in range(len(threads)):
            threads[i].join()

        # Проверяем наличие ошибок
        if all(isinstance(val, Exception) for val in connections):
            DEVICE_SESSIONS.delete_pool(self.ip)
            raise connections[0]

        self.connections = [conn for conn in connections if not isinstance(conn, Exception)]

        # Сохраняем новые сессии, если было указано хранение глобально.
        # Но для начала очистим пул от возможных не сброшенных подключений.
        DEVICE_SESSIONS.clear_pool(self.ip)
        DEVICE_SESSIONS.add_connections_to_pool(
            self.ip, pool_size=self.pool_size, connections=connections
        )

        return self.connections[0]

    def _add_device_session(self, result_list: list, append_exc=True) -> None:
        tries = 3
        while tries > 0:
            try:
                logger.debug(f"Создаем сессию для {self.ip}")
                connection = DeviceFactory(
                    ip=self.ip,
                    protocol=self.protocol,
                    auth_obj=self.auth_obj,
                    snmp_community=self.snmp_community,
                ).get_session()

            except Exception as exc:
                logger.error(f"Ошибка при создании сессии {self.ip}", exc_info=exc)
                if tries == 1 and append_exc:
                    result_list.append(exc)
                    return
            else:
                logger.debug(f"Успешно создали сессию для {self.ip}")
                result_list.append(connection)
                return
            finally:
                tries -= 1

    def _check_and_expand_to_pool_size(self) -> None:
        pool = DEVICE_SESSIONS.get_or_create_pool(self.ip, self.pool_size)
        for i in range(self.pool_size - len(pool)):
            self._create_and_append_new_connection()
