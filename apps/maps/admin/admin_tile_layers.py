from django.contrib import admin
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin

from ..models import TileLayer


@admin.register(TileLayer)
class TileLayerAdmin(ModelAdmin):
    list_display = ("name", "crs", "url", "preview")
    search_fields = ("name", "url")
    list_filter = ("crs",)

    @admin.display(description="Preview")
    def preview(self, obj: TileLayer):
        url = obj.url.format(x=1, y=1, z=1, s="a")
        return mark_safe(f"<img src='{url}' alt='{obj.name}'>")
