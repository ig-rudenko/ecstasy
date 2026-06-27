from threading import Event, RLock, Thread

from django.test import SimpleTestCase

from devicemanager.session_control import SessionController
from devicemanager.vendors.base.device import BaseDevice


class LockingDevice:
    """Minimal device double for session lock tests."""

    def __init__(self):
        self._session_lock = RLock()

    def acquire_session(self, blocking: bool = True) -> bool:
        """Reserve the session for the current thread."""

        return self._session_lock.acquire(blocking=blocking)

    def release_session(self) -> None:
        """Release a session reservation owned by the current thread."""

        self._session_lock.release()

    @BaseDevice.lock_session
    def outer_method(self) -> str:
        """Call another method protected by the same session lock."""

        return self.inner_method()

    @BaseDevice.lock_session
    def inner_method(self) -> str:
        """Return a value while holding the session lock."""

        return "done"

    @BaseDevice.lock_session
    def failing_method(self) -> None:
        """Raise an error while holding the session lock."""

        raise RuntimeError("failure")


class SessionDouble(LockingDevice):
    """Device double accepted by the connection pool."""

    connection_protocol = "ssh"

    class Session:
        """Minimal terminal session double."""

        @staticmethod
        def isalive() -> bool:
            """Report the session as active."""

            return True

        @staticmethod
        def close() -> None:
            """Close the fake session."""

    session = Session()


class SessionLockTests(SimpleTestCase):
    """Tests for exclusive and reentrant terminal session access."""

    def test_decorator_initializes_lock_for_object_created_without_init(self):
        """A lightweight vendor double may call decorated methods without __init__."""

        device = LockingDevice.__new__(LockingDevice)

        self.assertEqual(device.inner_method(), "done")
        self.assertTrue(hasattr(device, "_session_lock"))

    def test_nested_decorated_method_does_not_deadlock(self):
        """One thread may re-enter the lock through another decorated method."""

        device = LockingDevice()
        completed = Event()

        def call_outer_method():
            device.outer_method()
            completed.set()

        thread = Thread(target=call_outer_method, daemon=True)
        thread.start()

        self.assertTrue(completed.wait(timeout=0.2))
        thread.join(timeout=0.2)

    def test_exception_releases_session_lock(self):
        """An exception does not block all subsequent session operations."""

        device = LockingDevice()
        with self.assertRaises(RuntimeError):
            device.failing_method()

        completed = Event()

        def call_inner_method():
            device.inner_method()
            completed.set()

        thread = Thread(target=call_inner_method, daemon=True)
        thread.start()

        self.assertTrue(completed.wait(timeout=0.2))
        thread.join(timeout=0.2)

    def test_pool_reserves_connection_before_returning_it(self):
        """Concurrent callers cannot receive the same reserved connection."""

        sessions = SessionController()
        connection = SessionDouble()
        sessions.add_connections_to_pool(
            "192.0.2.10",
            pool_size=1,
            pool_expired_seconds=2,
            connections=[connection],
        )

        first_connection = sessions.get_connection("192.0.2.10")
        second_acquired = Event()

        def get_second_connection():
            second_connection = sessions.get_connection("192.0.2.10")
            second_acquired.set()
            second_connection.release_session()

        thread = Thread(target=get_second_connection, daemon=True)
        thread.start()

        self.assertFalse(second_acquired.wait(timeout=0.05))
        first_connection.release_session()
        self.assertTrue(second_acquired.wait(timeout=0.2))
        thread.join(timeout=0.2)
