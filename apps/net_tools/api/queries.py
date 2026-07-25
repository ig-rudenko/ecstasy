import re
from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.net_tools.services.interface_finder.types import InterfaceFinderFilter
from devicemanager.vendors.base.helpers import range_to_numbers


class DescFinderQuerySerializer(serializers.Serializer):
    has_comment = serializers.BooleanField(default=False, help_text="Только с комментариями")
    device_name = serializers.CharField(allow_null=True, default=None)
    device_name_regex = serializers.CharField(allow_null=True, default=None)
    desc_pattern = serializers.CharField(allow_null=True, default=None)
    desc_pattern_regex = serializers.CharField(allow_null=True, default=None)
    interface = serializers.CharField(allow_null=True, default=None)
    interface_regex = serializers.CharField(allow_null=True, default=None)
    interface_status = serializers.CharField(allow_null=True, default=None)
    vlans_superset = serializers.ListField(
        child=serializers.CharField(),
        allow_null=True,
        default=None,
        help_text="Строгое попадание в диапазон. Пример: 1-20,70-100",
    )
    vlans = serializers.ListField(
        child=serializers.CharField(),
        allow_null=True,
        default=None,
        help_text="Любые из диапазона. Пример: 1-20,70-100",
    )
    vlans_exclude = serializers.ListField(
        child=serializers.CharField(),
        allow_null=True,
        default=None,
        help_text="Не должно быть. Пример: 1-20,70-100",
    )
    discovered_datetime_gt = serializers.DateTimeField(
        allow_null=True,
        default=None,
        help_text="Дата обнаружения не раньше чем указанная",
    )

    def validate_vlans_superset(self, value: list[str]) -> set[int] | None:
        return self._get_vlans(value)

    def validate_vlans(self, value: list[str]) -> set[int] | None:
        return self._get_vlans(value)

    def validate_vlans_exclude(self, value: list[str]) -> set[int] | None:
        return self._get_vlans(value)

    @staticmethod
    def _get_vlans(value: list[str]) -> set[int] | None:
        if not value:
            return None
        result: set[int] = set()

        for item in value:
            result.update(set(range_to_numbers(item)))

        return result or None

    @staticmethod
    def validate_desc_pattern_regex(value):
        if not value:
            return value
        try:
            return re.compile(value, flags=re.IGNORECASE)
        except re.PatternError as exc:
            raise ValidationError("Invalid regular expression pattern.") from exc

    @staticmethod
    def validate_device_name_regex(value):
        if not value:
            return value
        try:
            return re.compile(value, flags=re.IGNORECASE)
        except re.PatternError as exc:
            raise ValidationError("Invalid regular expression pattern.") from exc

    @staticmethod
    def validate_interface_regex(value):
        if not value:
            return value
        try:
            return re.compile(value, flags=re.IGNORECASE)
        except re.PatternError as exc:
            raise ValidationError("Invalid regular expression pattern.") from exc

    def validate(self, attrs: Any) -> Any:
        if not attrs["desc_pattern"] and not attrs["desc_pattern_regex"]:
            raise ValidationError("Необходимо указать `desc_pattern` или `desc_pattern_regex`")
        return attrs

    def create(self, validated_data: Any) -> InterfaceFinderFilter:

        return InterfaceFinderFilter(
            has_comment=validated_data["has_comment"],
            device_name=validated_data["device_name"] or validated_data["device_name_regex"],
            description_pattern=validated_data["desc_pattern"] or validated_data["desc_pattern_regex"],
            interface_name=validated_data["interface"] or validated_data["interface_regex"],
            interface_status=validated_data["interface_status"],
            vlans_superset=validated_data["vlans_superset"],
            vlans=validated_data["vlans"],
            vlans_exclude=validated_data["vlans_exclude"],
            discovered_datetime_gt=validated_data["discovered_datetime_gt"],
        )
