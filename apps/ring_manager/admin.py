from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RelatedDropdownFilter

from ecstasy_project.admin_filters import distinct_dropdown_filter

from .models import RingDev, TransportRing

RingNameDropdownFilter = distinct_dropdown_filter("ring_name", "ring name")


@admin.register(TransportRing)
class TransportRingAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = ["name", "status", "solution_time"]
    readonly_fields = ["status", "solutions", "solution_time"]
    filter_horizontal = ["users"]
    autocomplete_fields = ["head", "tail"]
    search_fields = ["name", "description"]
    list_filter = [("status", ChoicesDropdownFilter)]
    list_select_related = ["head", "tail"]
    fieldsets = (
        ("Основное", {"classes": ("tab",), "fields": ("name", "description", "users")}),
        ("Топология", {"classes": ("tab",), "fields": ("head", "tail", "vlans")}),
        ("Состояние", {"classes": ("tab", "collapse"), "fields": ("status", "solution_time", "solutions")}),
    )


@admin.register(RingDev)
class RingDevsAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = ["device", "ring_name", "next_dev", "prev_dev"]
    list_filter = [("device", RelatedDropdownFilter), RingNameDropdownFilter]
    search_fields = ["device__name", "ring_name"]
    autocomplete_fields = ["device", "next_dev", "prev_dev"]
    list_select_related = ["device", "next_dev", "next_dev__device", "prev_dev", "prev_dev__device"]

    def get_queryset(self, request):
        """Load only fields required for changelist display."""
        return (
            super()
            .get_queryset(request)
            .select_related("device", "next_dev", "next_dev__device", "prev_dev", "prev_dev__device")
            .only(
                "id",
                "ring_name",
                "device__id",
                "device__name",
                "device__ip",
                "next_dev__id",
                "next_dev__ring_name",
                "next_dev__device__id",
                "next_dev__device__name",
                "next_dev__device__ip",
                "prev_dev__id",
                "prev_dev__ring_name",
                "prev_dev__device__id",
                "prev_dev__device__name",
                "prev_dev__device__ip",
            )
        )
