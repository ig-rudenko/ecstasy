import os

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


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
        upload_to="media",
        verbose_name="Слой будет взят из файла",
        help_text="Файл должен быть GEOJSON",
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
        help_text="Для узла сети Zabbix",
    )
    points_border_color = models.CharField(
        max_length=10,
        default="#ffffff",
        verbose_name="Цвет рамки маркера",
        help_text="Для узла сети Zabbix",
    )
    points_radius = models.PositiveSmallIntegerField(
        default=7,
        verbose_name="Радиус маркеров для",
        help_text="Для узла сети Zabbix",
        validators=[MinValueValidator(1), MaxValueValidator(20)],
    )

    def __str__(self) -> str:
        return f"[{self.type}] Layer:({self.name})"

    @property
    def type(self):
        if self.from_file:
            return "file"
        if self.zabbix_group_name:
            return "zabbix"

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        """
        При сохранении в БД проверяем,
        если старый файл существует, а новый файл отличается, удалите старый файл
        """
        try:
            # Он получает старый файл из базы данных.
            old_file = Layers.objects.get(id=self.id).from_file
            # Он проверяет, существует ли старый файл и отличается ли новый файл.
            if (
                old_file
                and not self.from_file
                or old_file
                and self.from_file.path != old_file.path
            ):
                # Удаляем предыдущий файл
                if os.path.exists(old_file.path):
                    os.remove(old_file.path)
        # Он перехватывает исключение, возникающее при попытке получить несуществующий объект.
        except Layers.DoesNotExist:
            pass

        # Вызов метода сохранения родительского класса.
        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    def delete(self, using=None, keep_parents=False):
        """
        При удалении экземпляра модели также удаляем и файл, если он есть

        :param using: База данных для использования. Оставьте пустым, чтобы использовать базу данных по умолчанию
        :param keep_parents: Если True, не удаляйте родительскую модель, defaults to False (optional)
        """
        # Старый файл из базы данных.
        old_file = Layers.objects.get(id=self.id).from_file

        if os.path.exists(old_file.path):
            # Удаление файла.
            os.remove(old_file.path)

        # Вызов метода удаления родительского класса.
        return super().delete(using, keep_parents)


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

    def __str__(self):
        return f"Map: {self.name}"

    @property
    def type(self):
        if self.map_url:
            return "external"
        if self.layers:
            return "zabbix"
