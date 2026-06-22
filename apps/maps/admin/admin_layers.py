from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe
from unfold.admin import ModelAdmin

from ..models import Layers
from .admin_forms import LayerFrom
from .admin_utils import (
    get_icons_html_code,
    get_line,
    get_polygon,
    parse_layer_file,
    resolve_marker_icon,
    svg_device_icon,
    svg_file_icon,
    svg_zabbix_icon,
)


@admin.register(Layers)
class LayersAdmin(ModelAdmin):
    list_display = ("layer_name", "icon", "layer_type", "description", "download_layer")
    form = LayerFrom
    search_fields = ("name", "description")
    fieldsets = (
        ("Описание", {"fields": ("name", "description"), "classes": ("tab", "wide")}),
        ("Из файла", {"fields": ("from_file",), "classes": ("tab", "wide")}),
        ("Из Zabbix", {"fields": ("zabbix_group_name",), "classes": ("tab", "wide")}),
        ("Из группы оборудования", {"fields": ("device_group",), "classes": ("tab", "wide")}),
        (
            "Настройки по умолчанию для Маркера",
            {
                "fields": ("points_color", "points_border_color", "points_size", "marker_icon_name"),
                "classes": ("tab", "wide"),
            },
        ),
        (
            "Настройки по умолчанию для Полигона",
            {
                "fields": ("polygon_opacity", "polygon_fill_color", "polygon_border_color"),
                "classes": ("tab", "wide"),
            },
        ),
    )

    @admin.display(description="Скачать слой")
    def download_layer(self, instance: Layers):
        if instance.type == "file":
            return format_html(
                """<a href="{}" target="_blank"><svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" viewBox="0 0 16 16"><path d="M9.293 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.707A1 1 0 0 0 13.707 4L10 .293A1 1 0 0 0 9.293 0M9.5 3.5v-2l3 3h-2a1 1 0 0 1-1-1m-1 4v3.793l1.146-1.147a.5.5 0 0 1 .708.708l-2 2a.5.5 0 0 1-.708 0l-2-2a.5.5 0 0 1 .708-.708L7.5 11.293V7.5a.5.5 0 0 1 1 0"/></svg></a>""",
                instance.from_file.url,
            )
        return ""

    @admin.display(description="Название слоя")
    def layer_name(self, instance: Layers) -> str:
        if instance.type == "zabbix":
            return format_html("{} {}", mark_safe(svg_zabbix_icon), instance.name)
        if instance.type == "file":
            return format_html("{} {}", mark_safe(svg_file_icon), instance.name)
        if instance.type == "device_group":
            return format_html("{} {}", mark_safe(svg_device_icon), instance.name)
        return instance.name

    @admin.display(description="Структура")
    def icon(self, instance: Layers) -> SafeString:
        if instance.type == "zabbix":
            html = get_icons_html_code(
                instance.points_color, instance.points_border_color, icon_name="circle-fill"
            )
        elif instance.type == "device_group":
            html = resolve_marker_icon(
                instance.points_color, instance.points_border_color, instance.marker_icon_name
            )
        else:
            try:
                file_info = parse_layer_file(instance.from_file.path)
            except Exception as exc:
                return format_html('<div style="color: red">{}</div>', exc)
            html = ""
            if file_info.get("Point"):
                html += resolve_marker_icon(
                    instance.points_color, instance.points_border_color, instance.marker_icon_name
                )
            if file_info.get("Polygon"):
                colors = file_info["Polygon"]["colours"].most_common(1)
                main_color = colors[0][0] if colors else instance.polygon_fill_color
                html += get_polygon(fill_color=main_color)
            if file_info.get("LineString"):
                colors = file_info["LineString"]["colours"].most_common(1)
                main_color = colors[0][0] if colors else instance.polygon_border_color
                html += get_line(fill_color=main_color)
        return mark_safe(html)  # type: ignore[arg-type]

    @admin.display(description="Тип слоя")
    def layer_type(self, instance: Layers):
        if instance.from_file:
            return mark_safe(
                f'{svg_file_icon} <strong>"{str(instance.from_file.name).rsplit("/", 1)[-1]}"</strong>'
            )
        if instance.zabbix_group_name:
            return mark_safe(f'{svg_zabbix_icon} - <strong>"{instance.zabbix_group_name}"</strong>')
        if instance.device_group:
            return format_html('Группа оборудования - <strong>"{}"</strong>', instance.device_group.name)
        return "Неизвестный тип слоя"
