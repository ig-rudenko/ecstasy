import hashlib

from django.db import migrations, models


def populate_tile_layer_url_hash(apps, schema_editor):
    """Заполнить хэши URL для уже существующих картографических подложек."""

    tile_layer_model = apps.get_model("maps", "TileLayer")
    db_alias = schema_editor.connection.alias

    for tile_layer in tile_layer_model.objects.using(db_alias).iterator():
        tile_layer.url_hash = hashlib.sha256(tile_layer.url.encode("utf-8")).hexdigest()
        tile_layer.save(update_fields=["url_hash"])


class Migration(migrations.Migration):
    dependencies = [
        ("maps", "0013_tilelayer"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tilelayer",
            name="url",
            field=models.URLField(
                help_text="Шаблон URL с параметрами {x}, {y}, {z}",
                max_length=2048,
                verbose_name="URL тайлов",
            ),
        ),
        migrations.AddField(
            model_name="tilelayer",
            name="url_hash",
            field=models.CharField(
                editable=False,
                max_length=64,
                null=True,
                verbose_name="Хэш URL тайлов",
            ),
        ),
        migrations.RunPython(populate_tile_layer_url_hash, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="tilelayer",
            name="url_hash",
            field=models.CharField(
                editable=False,
                max_length=64,
                unique=True,
                verbose_name="Хэш URL тайлов",
            ),
        ),
    ]
