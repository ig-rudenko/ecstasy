from django.db import migrations

LEGACY_PERMISSION_CODENAME = "device_bras_read_write"
NEW_PERMISSION_CODENAME = "device_interface_change_desc"
NEW_PERMISSION_NAME = "Изменение описания порта"


def add_interface_change_description_permission(apps, schema_editor) -> None:
    """Create the new permission and copy direct user and group assignments."""
    ContentType = apps.get_model("contenttypes", "ContentType")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    User = apps.get_model("accounting", "User")
    db_alias = schema_editor.connection.alias

    content_type, _ = ContentType.objects.using(db_alias).get_or_create(
        app_label="check",
        model="profile",
    )
    new_permission, _ = Permission.objects.using(db_alias).get_or_create(
        codename=NEW_PERMISSION_CODENAME,
        content_type=content_type,
        defaults={"name": NEW_PERMISSION_NAME},
    )
    legacy_permission = (
        Permission.objects.using(db_alias)
        .filter(
            codename=LEGACY_PERMISSION_CODENAME,
            content_type=content_type,
        )
        .first()
    )
    if legacy_permission is None:
        return

    user_permissions = User.user_permissions.through
    direct_user_ids = (
        user_permissions.objects.using(db_alias)
        .filter(permission_id=legacy_permission.pk)
        .values_list("user_id", flat=True)
    )
    user_permissions.objects.using(db_alias).bulk_create(
        [
            user_permissions(user_id=user_id, permission_id=new_permission.pk)
            for user_id in direct_user_ids.iterator()
        ],
        ignore_conflicts=True,
    )

    group_permissions = Group.permissions.through
    group_ids = (
        group_permissions.objects.using(db_alias)
        .filter(permission_id=legacy_permission.pk)
        .values_list("group_id", flat=True)
    )
    group_permissions.objects.using(db_alias).bulk_create(
        [
            group_permissions(group_id=group_id, permission_id=new_permission.pk)
            for group_id in group_ids.iterator()
        ],
        ignore_conflicts=True,
    )


def remove_interface_change_description_permission(apps, schema_editor) -> None:
    """Remove the new permission and all assignments when reversing."""
    Permission = apps.get_model("auth", "Permission")
    db_alias = schema_editor.connection.alias
    Permission.objects.using(db_alias).filter(
        codename=NEW_PERMISSION_CODENAME,
        content_type__app_label="check",
        content_type__model="profile",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0004_move_user_to_accounting_table"),
        ("check", "0043_profile_permissions_to_auth_permissions"),
    ]

    operations = [
        migrations.RunPython(
            add_interface_change_description_permission,
            remove_interface_change_description_permission,
        ),
    ]
