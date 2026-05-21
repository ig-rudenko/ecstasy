from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import DiscoveryAttempt, DiscoveryCandidate, DiscoveryProfile, DiscoveryRun


@admin.register(DiscoveryProfile)
class DiscoveryProfileAdmin(ModelAdmin):
    """Администрирование профилей auto discovery."""

    list_display = ("name", "device_group", "auto_create", "is_active", "updated_at")
    list_filter = ("auto_create", "is_active", "port_scan_protocol", "cmd_protocol")
    search_fields = ("name",)
    filter_horizontal = ("auth_groups",)


@admin.register(DiscoveryRun)
class DiscoveryRunAdmin(ModelAdmin):
    """Администрирование запусков auto discovery."""

    list_display = ("id", "profile", "status", "processed", "total", "found", "created", "created_at")
    list_filter = ("status", "dry_run")
    search_fields = ("task_id", "profile__name")
    readonly_fields = ("task_id", "created_at", "started_at", "finished_at")


@admin.register(DiscoveryCandidate)
class DiscoveryCandidateAdmin(ModelAdmin):
    """Администрирование кандидатов auto discovery."""

    list_display = ("ip", "name", "vendor", "model", "status", "confidence", "last_seen_at")
    list_filter = ("status", "source", "vendor")
    search_fields = ("ip", "name", "vendor", "model", "serial_number", "sys_name")
    readonly_fields = ("first_seen_at", "last_seen_at", "raw_fingerprint")


@admin.register(DiscoveryAttempt)
class DiscoveryAttemptAdmin(ModelAdmin):
    """Администрирование попыток auto discovery."""

    list_display = ("ip", "method", "status", "duration_ms", "created_at")
    list_filter = ("method", "status")
    search_fields = ("ip", "error")
    readonly_fields = ("created_at",)
