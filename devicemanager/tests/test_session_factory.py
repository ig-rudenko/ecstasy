from queue import Queue
from threading import Event, Lock, Thread
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from devicemanager.dc import SimpleAuthObject
from devicemanager.device_connector.exceptions import MethodError
from devicemanager.device_connector.factory import DeviceSessionFactory
from devicemanager.exceptions import DeviceException, SSHConnectionError
from devicemanager.session_control import ConnectionPool, GlobalSession, SessionController


class DeviceSessionFactoryTests(SimpleTestCase):
    """Tests for device session pool creation."""

    def setUp(self):
        """Use an isolated session controller for every test."""

        self.sessions = SessionController()
        self.sessions_patcher = patch(
            "devicemanager.device_connector.factory.DEVICE_SESSIONS",
            self.sessions,
        )
        self.sessions_patcher.start()
        self.addCleanup(self.sessions_patcher.stop)

    @staticmethod
    def make_factory(pool_size: int = 1) -> DeviceSessionFactory:
        """Create a factory suitable for isolated connection tests."""

        return DeviceSessionFactory(
            ip="192.0.2.10",
            protocol="ssh",
            auth_obj=SimpleAuthObject(login="user", password="password"),
            make_session_global=True,
            pool_size=pool_size,
            snmp_community="public",
            port_scan_protocol="ssh",
        )

    def test_empty_pool_is_not_replaced_during_initialization(self):
        """Repeated lookup returns the same pending pool instance."""

        first_pool = self.sessions.get_or_create_pool("192.0.2.10", pool_size=2)
        second_pool = self.sessions.get_or_create_pool("192.0.2.10", pool_size=2)

        self.assertIs(second_pool, first_pool)

    def test_first_failed_attempt_does_not_hide_successful_connection(self):
        """A later successful parallel attempt wins over an earlier error."""

        queue = Queue(maxsize=2)
        connection = Mock()
        queue.put(SSHConnectionError("SSH недоступен", ip="192.0.2.10"))
        queue.put(connection)

        result = DeviceSessionFactory.get_first_valid_connection(queue)

        self.assertIs(result, connection)

    def test_pool_connections_include_activity_and_protocol(self):
        """Pool diagnostics expose actual protocol stored on every connection."""

        connection = Mock(connection_protocol="ssh", lock=False)
        connection.session.isalive.return_value = True
        self.sessions.add_connections_to_pool(
            "192.0.2.10",
            pool_size=1,
            connections=[connection],
        )

        self.assertEqual(
            self.sessions.get_pool_connections("192.0.2.10"),
            [{"active": True, "protocol": "ssh"}],
        )

    def test_pool_does_not_return_connection_closed_while_waiting(self):
        """A connection must still be alive after its reservation becomes available."""

        connection = Mock()
        connection.session.isalive.side_effect = [True, False]
        connection.acquire_session.side_effect = [False, True]
        pool = ConnectionPool(max_size=1)
        pool.add(GlobalSession(connection=connection))

        result = pool.get()

        self.assertIsNone(result)
        connection.release_session.assert_called_once_with()

    @patch("devicemanager.device_connector.factory.DeviceRemoteConnector.get_session")
    def test_failed_creation_removes_pending_pool(self, get_session):
        """A failed creation does not leave a permanently pending pool."""

        get_session.side_effect = SSHConnectionError("SSH недоступен", ip="192.0.2.10")

        with self.assertRaises(SSHConnectionError):
            self.make_factory()._make_and_get_connection()

        self.assertFalse(self.sessions.has_pool("192.0.2.10"))

    @patch("devicemanager.device_connector.factory.DeviceRemoteConnector.get_session")
    def test_concurrent_requests_share_failed_creation_attempt(self, get_session):
        """Concurrent callers receive one creation attempt result."""

        creation_started = Event()
        waiter_started = Event()
        release_creation = Event()
        errors = []
        original_wait = ConnectionPool.wait_until_created

        def fail_connection():
            creation_started.set()
            release_creation.wait(timeout=1)
            raise SSHConnectionError("SSH недоступен", ip="192.0.2.10")

        def wait_until_created(pool, timeout):
            waiter_started.set()
            return original_wait(pool, timeout)

        def connect():
            try:
                self.make_factory()._make_and_get_connection()
            except Exception as exc:  # noqa: BLE001 - test records the propagated error type.
                errors.append(exc)

        get_session.side_effect = fail_connection
        with patch.object(ConnectionPool, "wait_until_created", wait_until_created):
            creator = Thread(target=connect)
            waiter = Thread(target=connect)
            creator.start()
            self.assertTrue(creation_started.wait(timeout=1))
            waiter.start()
            self.assertTrue(waiter_started.wait(timeout=1))
            release_creation.set()
            creator.join(timeout=1)
            waiter.join(timeout=1)

        self.assertFalse(creator.is_alive())
        self.assertFalse(waiter.is_alive())
        self.assertEqual(get_session.call_count, 1)
        self.assertEqual(len(errors), 2)
        self.assertTrue(all(isinstance(error, SSHConnectionError) for error in errors))

    @patch("devicemanager.device_connector.factory.DeviceRemoteConnector.get_session")
    def test_concurrent_requests_do_not_duplicate_pool_expansion(self, get_session):
        """A waiter does not start another expansion while the initial batch runs."""

        all_connections_started = Event()
        waiter_started = Event()
        release_connections = Event()
        call_count_lock = Lock()
        original_wait = ConnectionPool.wait_until_created
        connections = [Mock(lock=False), Mock(lock=False)]
        created_connections = 0
        results = []

        for connection in connections:
            connection.session.isalive.return_value = True

        def create_connection():
            nonlocal created_connections
            with call_count_lock:
                call_index = created_connections
                created_connections += 1
                if created_connections == 2:
                    all_connections_started.set()
            release_connections.wait(timeout=1)
            return connections[call_index]

        def wait_until_created(pool, timeout):
            waiter_started.set()
            return original_wait(pool, timeout)

        def connect():
            results.append(self.make_factory(pool_size=2)._make_and_get_connection())

        get_session.side_effect = create_connection
        with patch.object(ConnectionPool, "wait_until_created", wait_until_created):
            creator = Thread(target=connect)
            waiter = Thread(target=connect)
            creator.start()
            self.assertTrue(all_connections_started.wait(timeout=1))
            waiter.start()
            self.assertTrue(waiter_started.wait(timeout=1))
            release_connections.set()
            creator.join(timeout=1)
            waiter.join(timeout=1)

        self.assertFalse(creator.is_alive())
        self.assertFalse(waiter.is_alive())
        self.assertEqual(get_session.call_count, 2)
        self.assertEqual(len(results), 2)

    @patch("devicemanager.device_connector.factory.DeviceRemoteConnector.get_session")
    def test_late_connection_is_closed_after_creation_timeout(self, get_session):
        """A session completed after the pool deadline is closed."""

        creation_started = Event()
        release_creation = Event()
        connection_closed = Event()
        connection = Mock()
        connection.session.close.side_effect = connection_closed.set

        def create_late_connection():
            creation_started.set()
            release_creation.wait(timeout=1)
            return connection

        get_session.side_effect = create_late_connection
        with (
            patch("devicemanager.device_connector.factory.SESSION_CREATION_TIMEOUT", 0.01),
            self.assertRaises(DeviceException),
        ):
            self.make_factory()._make_and_get_connection()

        self.assertTrue(creation_started.is_set())
        release_creation.set()
        self.assertTrue(connection_closed.wait(timeout=1))
        self.assertFalse(self.sessions.has_pool("192.0.2.10"))

    def test_non_global_connection_is_closed_after_successful_method(self):
        """A one-shot connection is closed after its method completes."""

        factory = self.make_factory()
        factory.make_session_global = False
        connection = Mock()
        connection.get_system_info.return_value = {"vendor": "test"}

        with patch.object(factory, "_get_connection_to_perform", return_value=connection):
            result = factory._perform("get_system_info")

        self.assertEqual(result, {"vendor": "test"})
        connection.session.close.assert_called_once_with()

    def test_global_connection_is_released_after_successful_method(self):
        """A pooled connection is released after its method completes."""

        factory = self.make_factory()
        connection = Mock()
        connection.get_system_info.return_value = {"vendor": "test"}

        with patch.object(factory, "_get_connection_to_perform", return_value=connection):
            result = factory._perform("get_system_info")

        self.assertEqual(result, {"vendor": "test"})
        connection.release_session.assert_called_once_with()

    def test_global_connection_is_released_after_failed_method(self):
        """A pooled connection is released when its method raises an error."""

        factory = self.make_factory()
        connection = Mock()
        connection.get_system_info.side_effect = RuntimeError("failure")

        with (
            patch.object(factory, "_get_connection_to_perform", return_value=connection),
            self.assertRaises(RuntimeError),
        ):
            factory._perform("get_system_info")

        connection.release_session.assert_called_once_with()

    def test_non_global_connection_is_closed_once_after_failed_method(self):
        """A one-shot connection is closed once when its method raises an error."""

        factory = self.make_factory()
        factory.make_session_global = False
        connection = Mock()
        connection.get_system_info.side_effect = RuntimeError("failure")

        with (
            patch.object(factory, "_get_connection_to_perform", return_value=connection),
            self.assertRaises(RuntimeError),
        ):
            factory._perform("get_system_info")

        connection.session.close.assert_called_once_with()

    def test_unknown_method_releases_global_connection_without_closing_it(self):
        """An unsupported method does not discard a healthy pooled connection."""

        factory = self.make_factory()
        connection = Mock(spec=["session", "release_session"])

        with (
            patch.object(factory, "_get_connection_to_perform", return_value=connection),
            self.assertRaises(MethodError),
        ):
            factory._perform("unknown_method")

        connection.release_session.assert_called_once_with()
        connection.session.close.assert_not_called()
