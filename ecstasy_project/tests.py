from typing import cast
from unittest.mock import patch

from django.db.models import QuerySet
from django.test import SimpleTestCase, override_settings
from requests.exceptions import ConnectionError as RequestsConnectionError
from rest_framework import status
from rest_framework.exceptions import APIException, NotAcceptable, ValidationError

from apps.check.api.decorators import except_connection_errors
from ecstasy_project.error_handler import (
    PROBLEM_CONTENT_TYPE,
    PROBLEM_TYPES,
    DeviceConnectionProblem,
    build_problem,
    custom_exception_handler,
)
from ecstasy_project.task import ThreadUpdatedStatusTask


class FakeQuerySet:
    """Minimal queryset fake for task lifecycle tests."""

    def count(self) -> int:
        """Return one object for task initialization."""
        return 1

    def all(self) -> list[object]:
        """Return fake objects for worker dispatch."""
        return [object()]


class SuccessfulThreadTask(ThreadUpdatedStatusTask):
    """Thread task that completes successfully."""

    queryset = cast(QuerySet, FakeQuerySet())
    max_workers = 1

    def thread_task(self, obj, **kwargs) -> str:
        """Return a marker value from the worker body."""
        return "ok"


class FailingThreadTask(ThreadUpdatedStatusTask):
    """Thread task that raises from the worker body."""

    queryset = cast(QuerySet, FakeQuerySet())
    max_workers = 1

    def thread_task(self, obj, **kwargs) -> None:
        """Raise an error from the worker body."""
        raise RuntimeError("boom")


class ThreadUpdatedStatusTaskTests(SimpleTestCase):
    """Tests for threaded Celery task database connection cleanup."""

    @patch("ecstasy_project.task.connections.close_all")
    @patch("ecstasy_project.task.close_old_connections")
    def test_thread_task_closes_database_connections(self, close_old_connections, close_all) -> None:
        """Thread worker closes its Django DB connection after successful work."""
        task = SuccessfulThreadTask()

        result = task._run_thread_task(object())

        self.assertEqual(result, "ok")
        close_old_connections.assert_called_once_with()
        close_all.assert_called_once_with()

    @patch("ecstasy_project.task.connections.close_all")
    @patch("ecstasy_project.task.close_old_connections")
    def test_thread_task_closes_database_connections_after_error(
        self, close_old_connections, close_all
    ) -> None:
        """Thread worker closes its Django DB connection after failed work."""
        task = FailingThreadTask()

        with self.assertRaises(RuntimeError):
            task._run_thread_task(object())

        close_old_connections.assert_called_once_with()
        close_all.assert_called_once_with()


class ErrorHandlerTests(SimpleTestCase):
    """Tests for RFC 9457 problem details response building."""

    @override_settings(API_PROBLEM_BASE_URL="https://api.example.test/problems")
    def test_validation_error_has_problem_details_and_simplified_errors(self) -> None:
        """Validation errors contain standard members and simplified field paths."""
        problem = build_problem(
            exc=ValidationError(),
            data={"profile": {"color": ["Invalid color."]}, "title": ["This field is required."]},
            http_status=status.HTTP_400_BAD_REQUEST,
            title="Bad Request",
            instance="/api/example/",
        )

        self.assertEqual(problem["type"], "https://api.example.test/problems/validation-error")
        self.assertEqual(problem["title"], "Validation Error")
        self.assertEqual(problem["status"], status.HTTP_400_BAD_REQUEST)
        self.assertEqual(problem["detail"], "Request validation failed.")
        self.assertEqual(problem["instance"], "/api/example/")
        self.assertEqual(
            problem["errors"],
            [
                {"detail": "Invalid color.", "field": "profile.color"},
                {"detail": "This field is required.", "field": "title"},
            ],
        )

    def test_problem_types_declare_http_status_code(self) -> None:
        """Every configured problem type declares the HTTP status code it represents."""
        for exc_class, problem_type in PROBLEM_TYPES.items():
            with self.subTest(exc_class=exc_class):
                self.assertIsInstance(problem_type.status_code, int)
                self.assertGreaterEqual(problem_type.status_code, 400)
                self.assertLess(problem_type.status_code, 600)

    def test_known_api_exception_status_matches_problem_type_status(self) -> None:
        """Configured DRF exception statuses match their problem type definitions."""
        exc = NotAcceptable()
        problem = build_problem(
            exc=exc,
            data={"detail": exc.detail},
            http_status=exc.status_code,
            title="Not Acceptable",
            instance=None,
        )

        self.assertEqual(problem["status"], PROBLEM_TYPES[NotAcceptable].status_code)
        self.assertEqual(problem["title"], PROBLEM_TYPES[NotAcceptable].title)

    def test_unhandled_exception_returns_problem_response(self) -> None:
        """Unhandled exceptions are converted to an internal server error problem response."""
        response = custom_exception_handler(RuntimeError("boom"), {})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.content_type, PROBLEM_CONTENT_TYPE)
        self.assertEqual(response.data["title"], "Internal Server Error")
        self.assertEqual(response.data["status"], status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["detail"], "Unexpected server error.")

    def test_unknown_api_exception_uses_exception_status_code(self) -> None:
        """Unknown APIException subclasses still produce a complete problem type."""

        class Locked(APIException):
            status_code = 423
            default_code = "locked"
            default_detail = "Resource is locked."

        exc = Locked()
        problem = build_problem(
            exc=exc,
            data={"detail": exc.detail},
            http_status=exc.status_code,
            title="Locked",
            instance=None,
        )

        self.assertEqual(problem["type"], "/api/problems/locked")
        self.assertEqual(problem["title"], "Locked")
        self.assertEqual(problem["status"], 423)

    def test_connection_decorator_raises_problem_exception(self) -> None:
        """Connection decorator raises a problem exception instead of returning a response."""

        @except_connection_errors
        def broken_handler() -> None:
            raise RequestsConnectionError("connection refused")

        with self.assertRaises(DeviceConnectionProblem) as error:
            broken_handler()

        response = custom_exception_handler(error.exception, {})

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(response.content_type, PROBLEM_CONTENT_TYPE)
        self.assertEqual(response.data["type"], "/api/problems/device-connection-error")
        self.assertEqual(response.data["title"], "Device Connection Error")
        self.assertEqual(response.data["status"], status.HTTP_502_BAD_GATEWAY)
        self.assertIn("connection refused", response.data["detail"])
        self.assertEqual(response.data["errors"]["reason"], "ConnectionError")
