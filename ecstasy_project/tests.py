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
