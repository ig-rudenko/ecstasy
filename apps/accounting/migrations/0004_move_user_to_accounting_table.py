# Generated manually for the custom user model migration.

from django.db import migrations


def move_user_content_type(apps, schema_editor):
    """Move the existing auth.User content type to accounting.User."""
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    db_alias = schema_editor.connection.alias

    content_types = ContentType.objects.using(db_alias)
    permissions = Permission.objects.using(db_alias)
    old_content_type = content_types.filter(app_label="auth", model="user").first()
    new_content_type = content_types.filter(app_label="accounting", model="user").first()

    if old_content_type is None:
        return

    if new_content_type is not None and new_content_type.pk != old_content_type.pk:
        permissions.filter(content_type=new_content_type).delete()
        new_content_type.delete()

    old_content_type.app_label = "accounting"
    old_content_type.save(update_fields=["app_label"])


def restore_user_content_type(apps, schema_editor):
    """Restore the accounting.User content type back to auth.User."""
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    db_alias = schema_editor.connection.alias

    content_types = ContentType.objects.using(db_alias)
    permissions = Permission.objects.using(db_alias)
    old_content_type = content_types.filter(app_label="accounting", model="user").first()
    new_content_type = content_types.filter(app_label="auth", model="user").first()

    if old_content_type is None:
        return

    if new_content_type is not None and new_content_type.pk != old_content_type.pk:
        permissions.filter(content_type=new_content_type).delete()
        new_content_type.delete()

    old_content_type.app_label = "auth"
    old_content_type.save(update_fields=["app_label"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0003_userapitoken_allowed_ips"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.AlterModelTable(
            name="user",
            table=None,
        ),
        migrations.RunPython(move_user_content_type, restore_user_content_type),
    ]
