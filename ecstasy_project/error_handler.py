from __future__ import annotations

import traceback
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404, JsonResponse
from django.utils.encoding import force_str
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    MethodNotAllowed,
    NotAcceptable,
    NotAuthenticated,
    NotFound,
    ParseError,
    PermissionDenied,
    Throttled,
    UnsupportedMediaType,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

PROBLEM_CONTENT_TYPE = "application/problem+json"


class DeviceUnavailable(APIException):
    """Device cannot be queried right now."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Device unavailable."
    default_code = "device-unavailable"


class DeviceConnectionProblem(APIException):
    """Device connection failed while processing an API request."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "Device connection error."
    default_code = "device-connection-error"


class UnsupportedDeviceOperation(APIException):
    """Device does not support the requested operation."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Unsupported for this device."
    default_code = "unsupported-device-operation"


class DeviceCommandExecutionFailed(APIException):
    """Device command returned an invalid or failed result."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Device command execution failed."
    default_code = "device-command-execution-failed"


class ExternalServiceProblem(APIException):
    """External service failed or returned unusable data."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "External service error."
    default_code = "external-service-error"


class ConfigurationCollectionFailed(APIException):
    """Device configuration collection failed."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Configuration collection failed."
    default_code = "configuration-collection-failed"


class RingOperationFailed(APIException):
    """Ring manager operation failed."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Ring operation failed."
    default_code = "ring-operation-failed"


class ResourceConflict(APIException):
    """Requested operation conflicts with the current resource state."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "Resource state conflict."
    default_code = "resource-conflict"


@dataclass(frozen=True)
class ProblemType:
    slug: str
    title: str
    status_code: int


PROBLEM_TYPES: dict[type[Exception], ProblemType] = {
    DeviceUnavailable: ProblemType(
        "device-unavailable", "Device Unavailable", status.HTTP_503_SERVICE_UNAVAILABLE
    ),
    DeviceConnectionProblem: ProblemType(
        "device-connection-error",
        "Device Connection Error",
        status.HTTP_502_BAD_GATEWAY,
    ),
    UnsupportedDeviceOperation: ProblemType(
        "unsupported-device-operation",
        "Unsupported Device Operation",
        status.HTTP_400_BAD_REQUEST,
    ),
    DeviceCommandExecutionFailed: ProblemType(
        "device-command-execution-failed",
        "Device Command Execution Failed",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
    ExternalServiceProblem: ProblemType(
        "external-service-error", "External Service Error", status.HTTP_502_BAD_GATEWAY
    ),
    ConfigurationCollectionFailed: ProblemType(
        "configuration-collection-failed",
        "Configuration Collection Failed",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
    RingOperationFailed: ProblemType(
        "ring-operation-failed",
        "Ring Operation Failed",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
    ResourceConflict: ProblemType("resource-conflict", "Resource Conflict", status.HTTP_409_CONFLICT),
    ValidationError: ProblemType("validation-error", "Validation Error", status.HTTP_400_BAD_REQUEST),
    ParseError: ProblemType("parse-error", "Parse Error", status.HTTP_400_BAD_REQUEST),
    AuthenticationFailed: ProblemType(
        "authentication-failed", "Authentication Failed", status.HTTP_401_UNAUTHORIZED
    ),
    NotAuthenticated: ProblemType("not-authenticated", "Not Authenticated", status.HTTP_401_UNAUTHORIZED),
    PermissionDenied: ProblemType("permission-denied", "Permission Denied", status.HTTP_403_FORBIDDEN),
    DjangoPermissionDenied: ProblemType("permission-denied", "Permission Denied", status.HTTP_403_FORBIDDEN),
    NotFound: ProblemType("not-found", "Not Found", status.HTTP_404_NOT_FOUND),
    Http404: ProblemType("not-found", "Not Found", status.HTTP_404_NOT_FOUND),
    MethodNotAllowed: ProblemType(
        "method-not-allowed", "Method Not Allowed", status.HTTP_405_METHOD_NOT_ALLOWED
    ),
    NotAcceptable: ProblemType("not-acceptable", "Not Acceptable", status.HTTP_406_NOT_ACCEPTABLE),
    UnsupportedMediaType: ProblemType(
        "unsupported-media-type",
        "Unsupported Media Type",
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    ),
    Throttled: ProblemType("too-many-requests", "Too Many Requests", status.HTTP_429_TOO_MANY_REQUESTS),
}


def problem_type_url(slug: str) -> str:
    """Return the canonical URI for a problem type slug."""
    base_url = getattr(settings, "API_PROBLEM_BASE_URL", "/api/problems")
    return f"{base_url.rstrip('/')}/{slug}"


def get_problem_type(exc: Exception, fallback_title: str) -> ProblemType:
    """Return the configured problem type for an exception."""
    for exc_class, problem_type in PROBLEM_TYPES.items():
        if isinstance(exc, exc_class):
            return problem_type

    if isinstance(exc, APIException):
        return ProblemType(force_str(exc.default_code or "api-error"), fallback_title, exc.status_code)

    return ProblemType(
        "internal-server-error",
        "Internal Server Error",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def field_path(path: tuple[Any, ...]) -> str:
    """Convert a nested error path to the simplified dotted field path."""
    return ".".join(force_str(part) for part in path)


def normalize_errors(detail: Any, path: tuple[Any, ...] = ()) -> list[dict[str, str]]:
    """Normalize DRF validation details to the API error extension format."""
    if isinstance(detail, Mapping):
        errors: list[dict[str, str]] = []
        for key, value in detail.items():
            errors.extend(normalize_errors(value, (*path, key)))
        return errors

    if isinstance(detail, list | tuple):
        errors = []
        for index, value in enumerate(detail):
            if isinstance(value, Mapping):
                errors.extend(normalize_errors(value, (*path, index)))
            else:
                errors.extend(normalize_errors(value, path))
        return errors

    return [
        {
            "detail": force_str(detail),
            "field": field_path(path),
        }
    ]


def get_detail(data: Any, default: str) -> str:
    """Extract a human-readable problem detail from response data."""
    if isinstance(data, Mapping) and "detail" in data:
        return force_str(data["detail"])

    if isinstance(data, str):
        return data

    return default


def build_problem(
    *,
    exc: Exception,
    data: Any,
    http_status: int,
    title: str,
    instance: str | None,
) -> dict[str, Any]:
    """Build an RFC 9457 problem details object."""
    problem_type = get_problem_type(exc, title)

    problem: dict[str, Any] = {
        "type": problem_type_url(problem_type.slug),
        "title": problem_type.title,
        "status": http_status,
        "detail": get_detail(data, title),
    }

    if instance:
        problem["instance"] = instance

    if isinstance(exc, ValidationError):
        problem["detail"] = "Request validation failed."
        problem["errors"] = normalize_errors(data)
    elif isinstance(data, Mapping):
        extra_errors = {key: value for key, value in data.items() if key != "detail"}
        if extra_errors:
            problem["errors"] = extra_errors

    elif isinstance(data, list | tuple):
        problem["errors"] = normalize_errors(data)

    return problem


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    """Convert DRF exception responses to application/problem+json responses."""
    response = drf_exception_handler(exc, context)

    request = context.get("request")
    instance = request.get_full_path() if request else None

    if response is None:
        print(traceback.format_exc())
        problem = build_problem(
            exc=exc,
            data=None,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Internal Server Error",
            instance=instance,
        )
        problem["detail"] = "Unexpected server error."

        return Response(
            problem,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content_type=PROBLEM_CONTENT_TYPE,
        )

    problem = build_problem(
        exc=exc,
        data=response.data,
        http_status=response.status_code,
        title=response.status_text,
        instance=instance,
    )

    response.data = problem
    response.content_type = PROBLEM_CONTENT_TYPE

    return response


def django_problem_response(
    request,
    exc: Exception,
    http_status: int,
    title: str,
) -> JsonResponse:
    """Convert a standard Django error to a problem details response."""
    problem = build_problem(
        exc=exc,
        data={"detail": force_str(exc) or title},
        http_status=http_status,
        title=title,
        instance=request.get_full_path(),
    )
    response = JsonResponse(problem, status=http_status, content_type=PROBLEM_CONTENT_TYPE)
    response["Content-Type"] = PROBLEM_CONTENT_TYPE
    return response


def bad_request_handler(request, exception):
    """Handle standard Django 400 errors as problem details."""
    return django_problem_response(request, exception, status.HTTP_400_BAD_REQUEST, "Bad Request")


def permission_denied_handler(request, exception):
    """Handle standard Django 403 errors as problem details."""
    return django_problem_response(request, exception, status.HTTP_403_FORBIDDEN, "Permission Denied")


def not_found_handler(request, exception):
    """Handle standard Django 404 errors as problem details."""
    return django_problem_response(request, exception, status.HTTP_404_NOT_FOUND, "Not Found")


def server_error_handler(request):
    """Handle standard Django 500 errors as problem details."""
    problem = build_problem(
        exc=RuntimeError("Unexpected server error."),
        data={"detail": "Unexpected server error."},
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        instance=request.get_full_path(),
    )
    response = JsonResponse(
        problem,
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content_type=PROBLEM_CONTENT_TYPE,
    )
    response["Content-Type"] = PROBLEM_CONTENT_TYPE
    return response


def problem_type_document(request, slug: str) -> JsonResponse:
    """Return metadata for a registered problem type."""
    for problem_type in PROBLEM_TYPES.values():
        if problem_type.slug == slug:
            return JsonResponse(
                {
                    "type": problem_type_url(problem_type.slug),
                    "title": problem_type.title,
                    "status": problem_type.status_code,
                }
            )

    return not_found_handler(request, Http404(f"Problem type '{slug}' not found."))
