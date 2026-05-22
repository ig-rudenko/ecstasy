from rest_framework import serializers

from apps.check.models import AuthGroup, DeviceGroup

from ..models import DiscoveryCandidate, DiscoveryProfile, DiscoveryRun
from ..services.scanner import normalize_networks


class DiscoveryProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля auto discovery."""

    deviceGroup = serializers.PrimaryKeyRelatedField(
        source="device_group", queryset=DeviceGroup.objects.all()
    )
    authGroups = serializers.PrimaryKeyRelatedField(
        source="auth_groups",
        queryset=AuthGroup.objects.all(),
        many=True,
        required=False,
    )
    snmpCommunities = serializers.ListField(
        source="snmp_communities",
        child=serializers.CharField(max_length=64),
        write_only=True,
        required=False,
    )
    snmpCommunitiesCount = serializers.SerializerMethodField()
    tryProtocols = serializers.ListField(
        source="try_protocols",
        child=serializers.ChoiceField(choices=["ssh", "telnet"]),
        required=False,
    )
    portScanProtocol = serializers.ChoiceField(source="port_scan_protocol", choices=["snmp", "telnet", "ssh"])
    cmdProtocol = serializers.ChoiceField(source="cmd_protocol", choices=["telnet", "ssh"])
    maxWorkers = serializers.IntegerField(source="max_workers", min_value=1, max_value=80)
    timeoutSeconds = serializers.IntegerField(source="timeout_seconds", min_value=1, max_value=30)
    autoCreate = serializers.BooleanField(source="auto_create", required=False)
    autoCreateMinConfidence = serializers.IntegerField(
        source="auto_create_min_confidence",
        min_value=0,
        max_value=100,
        required=False,
    )
    isActive = serializers.BooleanField(source="is_active", required=False)

    class Meta:
        model = DiscoveryProfile
        fields = [
            "id",
            "name",
            "networks",
            "exclude_ips",
            "deviceGroup",
            "authGroups",
            "snmpCommunities",
            "snmpCommunitiesCount",
            "tryProtocols",
            "portScanProtocol",
            "cmdProtocol",
            "maxWorkers",
            "timeoutSeconds",
            "autoCreate",
            "autoCreateMinConfidence",
            "isActive",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "snmpCommunitiesCount"]

    @staticmethod
    def get_snmpCommunitiesCount(obj: DiscoveryProfile) -> int:
        """Вернуть количество SNMP community без раскрытия значений."""

        return len(obj.snmp_communities or [])

    @staticmethod
    def validate_networks(value: list[str]) -> list[str]:
        """Проверить список CIDR профиля discovery."""

        try:
            normalize_networks(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value

    def create(self, validated_data):
        """Создать профиль discovery с ManyToMany auth groups."""

        auth_groups = validated_data.pop("auth_groups", [])
        profile = super().create(validated_data)
        profile.auth_groups.set(auth_groups)
        return profile

    def update(self, instance, validated_data):
        """Обновить профиль discovery с ManyToMany auth groups."""

        auth_groups = validated_data.pop("auth_groups", None)
        profile = super().update(instance, validated_data)
        if auth_groups is not None:
            profile.auth_groups.set(auth_groups)
        return profile


class DiscoveryRunSerializer(serializers.ModelSerializer):
    """Сериализатор запуска auto discovery."""

    profileId = serializers.IntegerField(source="profile_id")
    createdBy = serializers.CharField(source="created_by.username", allow_null=True, read_only=True)

    class Meta:
        model = DiscoveryRun
        fields = [
            "id",
            "profileId",
            "task_id",
            "status",
            "total",
            "processed",
            "found",
            "created",
            "skipped",
            "errors",
            "dry_run",
            "summary",
            "createdBy",
            "started_at",
            "finished_at",
            "created_at",
        ]


class DiscoveryRunCreateSerializer(serializers.Serializer):
    """Сериализатор запроса запуска discovery."""

    profileId = serializers.PrimaryKeyRelatedField(source="profile", queryset=DiscoveryProfile.objects.all())
    networks = serializers.ListField(child=serializers.CharField(), required=False)
    dryRun = serializers.BooleanField(source="dry_run", default=False)

    @staticmethod
    def validate_networks(value: list[str]) -> list[str]:
        """Проверить override CIDR для запуска discovery."""

        try:
            normalize_networks(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value


class DiscoveryCandidateSerializer(serializers.ModelSerializer):
    """Сериализатор discovery candidate."""

    selectedAuthGroup = serializers.PrimaryKeyRelatedField(
        source="selected_auth_group",
        queryset=AuthGroup.objects.all(),
        required=False,
        allow_null=True,
    )
    selectedSnmpCommunitySet = serializers.SerializerMethodField()
    deviceId = serializers.IntegerField(source="device_id", allow_null=True, read_only=True)
    detectedProtocols = serializers.JSONField(source="detected_protocols")
    rawFingerprint = serializers.JSONField(source="raw_fingerprint", read_only=True)
    lastError = serializers.CharField(source="last_error", required=False, allow_blank=True)
    serialNumber = serializers.CharField(source="serial_number", required=False, allow_blank=True)
    osVersion = serializers.CharField(source="os_version", required=False, allow_blank=True)
    sysName = serializers.CharField(source="sys_name", required=False, allow_blank=True)
    sysDescr = serializers.CharField(source="sys_descr", required=False, allow_blank=True)
    sysObjectId = serializers.CharField(source="sys_object_id", required=False, allow_blank=True)
    macAddress = serializers.CharField(source="mac_address", required=False, allow_blank=True)
    selectedSnmpCommunity = serializers.CharField(
        source="selected_snmp_community",
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=64,
    )

    class Meta:
        model = DiscoveryCandidate
        fields = [
            "id",
            "ip",
            "name",
            "vendor",
            "model",
            "serialNumber",
            "osVersion",
            "macAddress",
            "sysName",
            "sysDescr",
            "sysObjectId",
            "source",
            "status",
            "confidence",
            "detectedProtocols",
            "selectedAuthGroup",
            "selectedSnmpCommunity",
            "selectedSnmpCommunitySet",
            "deviceId",
            "rawFingerprint",
            "lastError",
            "first_seen_at",
            "last_seen_at",
        ]
        read_only_fields = [
            "id",
            "ip",
            "source",
            "confidence",
            "selectedSnmpCommunitySet",
            "deviceId",
            "rawFingerprint",
            "first_seen_at",
            "last_seen_at",
        ]

    @staticmethod
    def get_selectedSnmpCommunitySet(obj: DiscoveryCandidate) -> bool:
        """Вернуть признак наличия SNMP community без раскрытия значения."""

        return bool(obj.selected_snmp_community)


class DiscoveryCandidateAcceptSerializer(serializers.Serializer):
    """Сериализатор подтверждения discovery candidate."""

    deviceGroup = serializers.PrimaryKeyRelatedField(queryset=DeviceGroup.objects.all(), required=False)
    authGroup = serializers.PrimaryKeyRelatedField(queryset=AuthGroup.objects.all(), required=False)
    cmdProtocol = serializers.ChoiceField(choices=["telnet", "ssh"], required=False)
    portScanProtocol = serializers.ChoiceField(choices=["snmp", "telnet", "ssh"], required=False)
    snmpCommunity = serializers.CharField(max_length=64, allow_blank=True, required=False)
    collectInterfaces = serializers.BooleanField(default=False)
