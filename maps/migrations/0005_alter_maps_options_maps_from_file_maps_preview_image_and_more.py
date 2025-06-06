# Generated by Django 4.1.2 on 2022-12-05 09:37

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("maps", "0004_alter_maps_layers_alter_maps_users"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="maps",
            options={"verbose_name": "Карту", "verbose_name_plural": "Карты"},
        ),
        migrations.AddField(
            model_name="maps",
            name="from_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="map_layer_files",
                verbose_name="HTML файл карты",
            ),
        ),
        migrations.AddField(
            model_name="maps",
            name="preview_image",
            field=models.ImageField(
                blank=True,
                help_text="Превью",
                null=True,
                upload_to="static/map_previews",
                verbose_name="Изображение карты",
            ),
        ),
        migrations.AlterField(
            model_name="layers",
            name="from_file",
            field=models.FileField(
                blank=True,
                help_text="Файл должен быть GEOJSON",
                null=True,
                upload_to="map_layer_files",
                verbose_name="Слой будет взят из файла",
            ),
        ),
        migrations.AlterField(
            model_name="maps",
            name="layers",
            field=models.ManyToManyField(blank=True, to="maps.layers", verbose_name="Cлои"),
        ),
        migrations.AlterField(
            model_name="maps",
            name="users",
            field=models.ManyToManyField(
                blank=True,
                help_text="Пользователи",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Выберите пользователей",
            ),
        ),
    ]
