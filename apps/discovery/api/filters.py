from django.db.models import Q, QuerySet
from django_filters import rest_framework as rf_filters

from ..models import DiscoveryCandidate

AUTH_CHECK_ERROR_FALLBACK = "Не удалось подключиться с AuthGroup из профиля discovery"
DISCOVERY_PROTOCOLS = {"ping", "snmp", "ssh", "telnet"}


class DiscoveryCandidateFilter(rf_filters.FilterSet):
    """Фильтры и сортировка списка discovery candidates."""

    search = rf_filters.CharFilter(method="filter_search")
    status = rf_filters.ChoiceFilter(choices=DiscoveryCandidate.Status.choices)
    vendor = rf_filters.CharFilter(lookup_expr="icontains")
    name = rf_filters.CharFilter(lookup_expr="icontains")
    ip = rf_filters.CharFilter(lookup_expr="icontains")
    model = rf_filters.CharFilter(lookup_expr="icontains")
    osVersion = rf_filters.CharFilter(field_name="os_version", lookup_expr="icontains")
    authCheckStatus = rf_filters.ChoiceFilter(
        field_name="auth_check_status_value",
        choices=[("SUCCESS", "Success"), ("FAILED", "Failed"), ("UNKNOWN", "Unknown")],
    )
    confidenceMin = rf_filters.NumberFilter(field_name="confidence", lookup_expr="gte")
    confidenceMax = rf_filters.NumberFilter(field_name="confidence", lookup_expr="lte")
    protocols = rf_filters.CharFilter(method="filter_protocols")
    lastError = rf_filters.CharFilter(field_name="last_error", lookup_expr="icontains")
    authCheckError = rf_filters.CharFilter(method="filter_auth_check_error")
    ordering = rf_filters.OrderingFilter(
        fields=(
            ("name", "name"),
            ("ip", "ip"),
            ("model", "model"),
            ("os_version", "osVersion"),
            ("status", "status"),
            ("confidence", "confidence"),
            ("auth_check_status_value", "authCheckStatus"),
            ("last_seen_at", "lastSeenAt"),
        )
    )

    class Meta:
        model = DiscoveryCandidate
        fields = [
            "search",
            "status",
            "vendor",
            "name",
            "ip",
            "model",
            "osVersion",
            "authCheckStatus",
            "confidenceMin",
            "confidenceMax",
            "protocols",
            "lastError",
            "authCheckError",
        ]

    @staticmethod
    def filter_search(queryset: QuerySet, name: str, value: str) -> QuerySet:
        """Отфильтровать кандидатов по имени или IP-адресу."""

        return queryset.filter(Q(name__icontains=value) | Q(ip__icontains=value))

    @staticmethod
    def filter_protocols(queryset: QuerySet, name: str, value: str) -> QuerySet:
        """Оставить кандидатов со всеми указанными обнаруженными протоколами."""

        protocols = {protocol.strip().lower() for protocol in value.split(",")}
        for protocol in protocols & DISCOVERY_PROTOCOLS:
            queryset = queryset.filter(**{f"detected_protocols__{protocol}": True})
        return queryset

    @staticmethod
    def filter_auth_check_error(queryset: QuerySet, name: str, value: str) -> QuerySet:
        """Отфильтровать кандидатов по вычисляемому тексту ошибки AuthGroup."""

        fallback_matches = value.casefold() in AUTH_CHECK_ERROR_FALLBACK.casefold()
        error_filter = Q(last_error__icontains=value)
        if fallback_matches:
            error_filter |= Q(last_error="")
        return queryset.filter(auth_check_status_value="FAILED").filter(error_filter)
