import os

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_delete, pre_save


class Layers(models.Model):
    class Meta:
        verbose_name = "Слой"
        verbose_name_plural = "Слои"

    name = models.CharField(
        max_length=100,
        null=False,
        verbose_name="Название слоя",
        help_text="Будет отображаться на карте",
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Подробное описание слоя",
    )

    from_file = models.FileField(
        null=True,
        blank=True,
        upload_to="map_layer_files",
        verbose_name="Слой будет взят из файла",
        help_text="Файл должен быть GEOJSON",
    )

    polygon_opacity = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        default=0.6,
        verbose_name="Непрозрачность полигона",
        help_text="Вещественное число от 0 до 1",
    )

    polygon_fill_color = models.CharField(
        max_length=7,
        default="#0074CC",
        verbose_name="Цвет полигона",
    )

    polygon_border_color = models.CharField(
        max_length=7,
        default="#004c87",
        verbose_name="Цвет рамок полигона",
    )

    zabbix_group_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Имя группы Zabbix",
        help_text="Все узлы сети из данной группы будут на этом слое",
    )

    points_color = models.CharField(
        max_length=10,
        default="#00CC00",
        verbose_name="Цвет маркера",
    )
    points_border_color = models.CharField(
        max_length=10,
        default="#ffffff",
        verbose_name="Цвет рамки маркера",
    )
    points_size = models.PositiveSmallIntegerField(
        default=7,
        verbose_name="Размер маркера (px)",
        validators=[MinValueValidator(2), MaxValueValidator(64)],
    )
    marker_icon_name = models.CharField(
        max_length=100,
        default="circle-fill",
        verbose_name="Выберите иконку",
    )

    def __str__(self) -> str:
        return f"[{self.type}] Layer:({self.name})"

    @property
    def type(self):
        if self.from_file:
            return "file"
        if self.zabbix_group_name:
            return "zabbix"


@receiver(pre_save, sender=Layers)
def update_file_for_layer(sender, instance: Layers, *args, **kwargs):
    try:
        # Он получает старый файл из базы данных.
        old_file = sender.objects.get(id=instance.id).from_file
        # Он проверяет, существует ли старый файл и отличается ли новый файл.
        if (
            old_file
            and not instance.from_file
            or old_file
            and instance.from_file.path != old_file.path
        ):
            # Удаляем предыдущий файл
            if os.path.exists(old_file.path):
                os.remove(old_file.path)
    # Он перехватывает исключение, возникающее при попытке получить несуществующий объект.
    except sender.DoesNotExist:
        pass


@receiver(post_delete, sender=Layers)
def remove_file_for_layer(sender, instance: Layers, *args, **kwargs):
    if os.path.exists(instance.from_file.path):
        os.remove(instance.from_file.path)


class Maps(models.Model):
    class Meta:
        verbose_name = "Карту"
        verbose_name_plural = "Карты"

    name = models.CharField(
        max_length=100,
        null=False,
        verbose_name="Название карты",
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Подробное описание карты",
    )

    interactive = models.BooleanField(
        default=False,
        verbose_name="Карта будет интерактивной?",
        help_text="Автоматическое обновление состояния узлов сети"
        " из тех слоев, что созданы через группу Zabbix",
    )

    from_file = models.FileField(
        null=True,
        blank=True,
        upload_to="templates/maps/external",
        verbose_name="HTML файл карты",
    )

    map_url = models.URLField(
        max_length=2048,
        null=True,
        blank=True,
        verbose_name="URL Карты из другого ресурса",
        help_text="URL должен быть абсолютным "
        "т.е. содержать обозначение протокола (`http://` или `https://`)",
    )

    layers = models.ManyToManyField(
        Layers,
        blank=True,
        verbose_name="Cлои",
    )

    users = models.ManyToManyField(
        User,
        blank=True,
        verbose_name="Выберите пользователей",
        help_text="Пользователи",
    )

    preview_image = models.ImageField(
        null=True,
        blank=True,
        upload_to="static/map_previews",
        verbose_name="Изображение карты",
        help_text="Превью",
    )

    def __str__(self):
        return f"Map: {self.name}"

    @property
    def type(self):
        if self.from_file:
            return "file"
        if self.map_url:
            return "external"
        if self.layers:
            return "zabbix"


@receiver(pre_save, sender=Maps)
def update_file_for_layer(sender, instance: Maps, *args, **kwargs):
    try:
        # Он получает старый файл из базы данных.
        old_instance: Maps = sender.objects.get(id=instance.id)
        old_file = old_instance.from_file
        old_image = old_instance.preview_image
        # Проверяем, существует ли старый файл и отличается ли от нового.
        if (
            old_file
            and not instance.from_file
            or old_file
            and instance.from_file.path != old_file.path
        ):
            # Удаляем предыдущий файл
            if os.path.exists(old_file.path):
                os.remove(old_file.path)

        # Проверяем, существует ли старое изоб и отличается ли от нового.
        if (
            old_image
            and not instance.preview_image
            or old_image
            and instance.preview_image.path != old_image.path
        ):
            # Удаляем предыдущий файл
            if os.path.exists(old_image.path):
                os.remove(old_image.path)

    # Он перехватывает исключение, возникающее при попытке получить несуществующий объект.
    except sender.DoesNotExist:
        pass


@receiver(post_delete, sender=Maps)
def remove_file_for_layer(sender, instance: Maps, *args, **kwargs):
    if os.path.exists(instance.preview_image.path):
        os.remove(instance.preview_image.path)
    if os.path.exists(instance.from_file.path):
        os.remove(instance.from_file.path)
