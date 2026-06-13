from collections.abc import Sequence

import orjson
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.check.models import Devices
from devicemanager.device import Interfaces


class DevicesInfo(models.Model):
    dev = models.OneToOneField(Devices, primary_key=True, on_delete=models.CASCADE)
    interfaces = models.TextField(null=True)
    interfaces_date = models.DateTimeField(null=True)
    vlans = models.TextField(null=True)
    vlans_date = models.DateTimeField(null=True)

    class Meta:
        db_table = "device_info"

    def update_interfaces_state(self, interfaces: Sequence | Interfaces):
        """Обновляет поле интерфейсов и время."""
        self.interfaces = self._parse_interfaces_to_json(interfaces, with_vlans=False)
        self.interfaces_date = timezone.now()

    def update_interfaces_with_vlans_state(self, interfaces: Sequence | Interfaces):
        """Обновляет поле интерфейсов и VLAN, а также время."""
        self.vlans = self._parse_interfaces_to_json(interfaces, with_vlans=True)
        self.vlans_date = timezone.now()

    @staticmethod
    def _parse_interfaces_to_json(interfaces: Sequence | Interfaces, with_vlans: bool) -> str:
        if isinstance(interfaces, Sequence):
            interfaces = Interfaces(interfaces)

        def get_intf_dict(interface) -> dict:
            res = {
                "name": interface.name,
                "status": interface.status,
                "description": interface.desc.strip(),
            }
            if with_vlans:
                res["vlans"] = interface.vlan
            return res

        interfaces_list = [get_intf_dict(line) for line in interfaces]
        return orjson.dumps(interfaces_list).decode()


class DescNameFormat(models.Model):
    standard = models.CharField(max_length=255, unique=True, verbose_name="Необходимое имя оборудования")
    replacement = models.TextField(verbose_name="Возможные варианты (через запятую)")

    class Meta:
        db_table = "traceroute_desc_name_format"
        verbose_name = "Traceroute desc name format"


class VlanName(models.Model):
    vid = models.PositiveIntegerField(
        primary_key=True,
        verbose_name="VLAN id",
        validators=[MinValueValidator(1), MaxValueValidator(4096)],
    )
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")

    def __str__(self):
        return f"{self.vid} ({self.name})"

    class Meta:
        db_table = "vlan_name"


class DevicesForMacSearch(models.Model):
    device = models.ForeignKey(
        Devices,
        on_delete=models.CASCADE,
        verbose_name="Оборудование для поиска MAC",
        help_text="Будет искать MAC в таблице arp оборудования",
    )
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="Описание")


class TracerouteNodeKind(models.Model):
    """Справочник семантических типов узлов трассировки."""

    class ValueSource(models.TextChoices):
        RAW = "raw", "Raw node value"
        MARKER_BODY = "marker_body", "Text inside marker"
        AFTER_ARROW = "after_arrow", "Text after '-->'"

    code = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Код типа",
        help_text="Стабильный технический код (например: empty_port, unknown_description, uplink_arrow).",
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Название типа",
        help_text="Человекочитаемое имя типа узла для админки.",
    )
    marker_prefix = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Префикс маркера",
        help_text="Маркер в сыром ID узла, по которому определяется этот тип (например: p:(, d:(, -->).",
    )
    marker_suffix = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Суффикс маркера",
        help_text="Закрывающая часть маркера (например: )). Для '-->' обычно пусто.",
    )
    value_source = models.CharField(
        max_length=32,
        choices=ValueSource.choices,
        default=ValueSource.RAW,
        verbose_name="Источник значения label",
    )
    hide_when_nodes_only = models.BooleanField(
        default=False,
        verbose_name="Скрывать в режиме only nodes",
        help_text="Если включено, узлы этого типа не будут добавляться в граф при nodes_only=true.",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Описание",
        help_text="Свободное описание назначения типа и примеров использования.",
    )

    class Meta:
        db_table = "traceroute_node_kind"
        verbose_name = "Traceroute node kind"
        verbose_name_plural = "Traceroute node kinds"

    def __str__(self) -> str:
        return f"{self.code}: {self.name}"


class TracerouteNodeStyleRule(models.Model):
    """Правило оформления узла графа трассировки."""

    class MatchType(models.TextChoices):
        CONTAINS = "contains", "Contains"
        EXACT = "exact", "Exact match"
        STARTS_WITH = "starts_with", "Starts with"
        ENDS_WITH = "ends_with", "Ends with"
        REGEX = "regex", "Regex"

    class Shape(models.TextChoices):
        DOT = "dot", "Dot"
        TRIANGLE = "triangle", "Triangle"
        SQUARE = "square", "Square"
        DIAMOND = "diamond", "Diamond"
        BOX = "box", "Box"

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Название правила",
        help_text="Уникальное имя правила для поддержки и отладки.",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активно",
        help_text="Выключенные правила игнорируются при построении графа.",
    )
    priority = models.PositiveSmallIntegerField(
        default=100,
        verbose_name="Приоритет",
        help_text="Чем меньше число, тем раньше применяется правило.",
    )
    node_kind = models.ForeignKey(
        TracerouteNodeKind,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="style_rules",
        verbose_name="Тип узла",
    )
    match_type = models.CharField(
        max_length=20,
        choices=MatchType.choices,
        default=MatchType.CONTAINS,
        verbose_name="Тип сопоставления",
    )
    pattern = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Шаблон сопоставления",
        help_text="Строка/regex для поиска в сыром имени узла. Пусто = без дополнительного условия.",
    )
    group_id = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Group color (legacy fallback)",
        help_text="Optional. Used only when explicit colors are not set below.",
    )
    color_background = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="Node background color",
        help_text="Any CSS color: #RRGGBB, rgb(...), hsl(...), var(--token).",
    )
    color_border = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="Node border color",
        help_text="Any CSS color.",
    )
    color_font = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="Node text color",
        help_text="Any CSS color.",
    )
    shape = models.CharField(
        max_length=20,
        choices=Shape.choices,
        null=True,
        blank=True,
        verbose_name="Форма узла",
        help_text="Форма узла vis-network. Если не задана, форма не меняется этим правилом.",
    )
    fixed_value = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Фиксированный размер узла",
        help_text="Если заполнено — подменяет auto value для узла.",
    )
    stop_processing = models.BooleanField(
        default=True,
        verbose_name="Остановить обработку после совпадения",
        help_text="Если включено, следующие правила для узла не применяются.",
    )
    description = models.TextField(blank=True, default="", verbose_name="Описание")

    class Meta:
        db_table = "traceroute_node_style_rule"
        verbose_name = "Traceroute node style rule"
        verbose_name_plural = "Traceroute node style rules"
        ordering = ("priority", "id")

    def __str__(self) -> str:
        return f"[{self.priority}] {self.name}"
