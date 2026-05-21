from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin

from ..models import Maps
from .admin_utils import svg_file_icon, svg_zabbix_icon


@admin.register(Maps)
class MapsAdmin(ModelAdmin):
    readonly_fields = ("map_image",)
    list_display = ("name", "map_image", "map_layers", "description", "url")
    filter_horizontal = ("users", "layers")
    search_fields = ("name", "description")
    fieldsets = (
        (
            "Основные",
            {"fields": ("name", "map_image", "preview_image", "description"), "classes": ("tab", "wide")},
        ),
        ("Файл карты", {"fields": ("from_file",), "classes": ("tab", "wide")}),
        ("Сторонняя карта по URL", {"fields": ("map_url",), "classes": ("tab", "wide")}),
        (
            "Укажите слои, из которых будет собрана карта",
            {"fields": ("interactive", "layers"), "classes": ("tab", "wide")},
        ),
        (
            "Укажите пользователей, которые будут иметь доступ к карте",
            {"fields": ("users",), "classes": ("tab", "wide")},
        ),
    )

    @admin.display(description="Открыть")
    def url(self, instance: Maps):
        return format_html(
            """<a href='/maps/{}' target='_blank'><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-box-arrow-right" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M10 12.5a.5.5 0 0 1-.5.5h-8a.5.5 0 0 1-.5-.5v-9a.5.5 0 0 1 .5-.5h8a.5.5 0 0 1 .5.5v2a.5.5 0 0 0 1 0v-2A1.5 1.5 0 0 0 9.5 2h-8A1.5 1.5 0 0 0 0 3.5v9A1.5 1.5 0 0 0 1.5 14h8a1.5 1.5 0 0 0 1.5-1.5v-2a.5.5 0 0 0-1 0z"/><path fill-rule="evenodd" d="M15.854 8.354a.5.5 0 0 0 0-.708l-3-3a.5.5 0 0 0-.708.708L14.293 7.5H5.5a.5.5 0 0 0 0 1h8.793l-2.147 2.146a.5.5 0 0 0 .708.708z"/></svg></a>""",
            instance.id,
        )

    @admin.display(description="Изображение")
    def map_image(self, instance: Maps):
        if instance.preview_image:
            return format_html('<img height="300" src="{}">', instance.preview_image.url)
        return "-"

    @admin.display(description="Структура")
    def map_layers(self, instance: Maps):
        text = ""
        if instance.type == "zabbix":
            text = "<h6>Слои:</h6>"
            for layer in instance.layers.all():
                if layer.type == "zabbix":
                    text += f'<li style="white-space: nowrap; color: {layer.points_color}">{svg_zabbix_icon} {layer.name}</li>'
                elif layer.type == "file":
                    text += f'<li style="white-space: nowrap;"> {svg_file_icon} {layer.name}</li>'
                else:
                    text += f"<li style='white-space: nowrap;'>{layer}</li>"
        elif instance.type == "external":
            text = f'<a href="{instance.map_url}" target="_blank">URL</a>'
        elif instance.type == "file":
            text = f'<p style="white-space: nowrap;">{svg_file_icon} {str(instance.from_file.name).rsplit("/", 1)[-1]}</p>'
        return mark_safe(text)
