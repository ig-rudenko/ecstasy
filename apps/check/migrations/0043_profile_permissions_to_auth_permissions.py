from django.db import migrations, models

PERMISSIONS = [
    ("device_interface_reboot", "Перезагрузка порта"),
    ("device_interface_up_down", "Изменение состояния порта"),
    ("device_bras_read", "Просмотр сессий BRAS"),
    ("device_bras_read_write", "Сброс сессий BRAS"),
    ("device_config_view", "Просмотр конфигураций оборудования"),
    ("device_config_collect", "Сбор конфигураций оборудования"),
    ("device_config_delete", "Удаление конфигураций оборудования"),
    ("device_cmd_run", "Выполнение команд"),
]

LEGACY_PERMISSION_MAP = [
    ("read", []),
    ("reboot", ["device_interface_reboot"]),
    ("up_down", ["device_interface_reboot", "device_interface_up_down"]),
    (
        "bras",
        [
            "device_interface_reboot",
            "device_interface_up_down",
            "device_bras_read",
            "device_bras_read_write",
            "device_config_view",
            "device_config_collect",
            "device_config_delete",
        ],
    ),
    (
        "cmd_run",
        [
            "device_interface_reboot",
            "device_interface_up_down",
            "device_bras_read",
            "device_bras_read_write",
            "device_config_view",
            "device_config_collect",
            "device_config_delete",
            "device_cmd_run",
        ],
    ),
]

REVERSE_LEGACY_PERMISSION_MAP = [
    ("cmd_run", ["device_cmd_run"]),
    (
        "bras",
        [
            "device_bras_read",
            "device_bras_read_write",
            "device_config_view",
            "device_config_collect",
            "device_config_delete",
        ],
    ),
    ("up_down", ["device_interface_up_down"]),
    ("reboot", ["device_interface_reboot"]),
]


def create_device_permissions(apps) -> dict[str, object]:
    """Create permissions needed before post_migrate hooks and return them by codename."""
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")

    content_type, _ = ContentType.objects.get_or_create(
        app_label="check",
        model="profile",
    )
    permissions = {}
    for codename, name in PERMISSIONS:
        permission, _ = Permission.objects.get_or_create(
            codename=codename,
            content_type=content_type,
            defaults={"name": name},
        )
        permissions[codename] = permission
    return permissions


def migrate_profile_permissions(apps, schema_editor) -> None:
    """Migrate legacy profile access level to cumulative device permissions."""
    Profile = apps.get_model("check", "Profile")
    User = apps.get_model("auth", "User")
    user_permissions = User.user_permissions.through
    permissions = create_device_permissions(apps)
    legacy_permission_map = dict(LEGACY_PERMISSION_MAP)

    for profile in Profile.objects.all():
        codenames = legacy_permission_map.get(profile.legacy_permissions, [])
        for codename in codenames:
            user_permissions.objects.get_or_create(
                user_id=profile.user_id,
                permission_id=permissions[codename].id,  # type: ignore
            )


def restore_profile_permissions(apps, schema_editor) -> None:
    """Restore legacy profile access level from device permissions."""
    Profile = apps.get_model("check", "Profile")
    User = apps.get_model("auth", "User")
    user_permissions = User.user_permissions.through
    permissions = create_device_permissions(apps)
    reverse_permission_map = {}
    for legacy_permission, codenames in REVERSE_LEGACY_PERMISSION_MAP:
        for codename in codenames:
            reverse_permission_map[permissions[codename].id] = legacy_permission  # type: ignore

    permission_ids_to_remove = set(reverse_permission_map)
    for profile in Profile.objects.all():
        permission_ids = set(
            user_permissions.objects.filter(
                user_id=profile.user_id,
                permission_id__in=reverse_permission_map,
            ).values_list("permission_id", flat=True)
        )
        profile.legacy_permissions = "read"
        for permission_id, legacy_permission in reverse_permission_map.items():
            if permission_id in permission_ids:
                profile.legacy_permissions = legacy_permission
                break
        profile.save(update_fields=["legacy_permissions"])
        user_permissions.objects.filter(
            user_id=profile.user_id,
            permission_id__in=permission_ids_to_remove,
        ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("check", "0042_bras_device"),
    ]

    operations = [
        migrations.RenameField(
            model_name="profile",
            old_name="permissions",
            new_name="legacy_permissions",
        ),
        migrations.RunPython(migrate_profile_permissions, restore_profile_permissions),
        migrations.RemoveField(
            model_name="profile",
            name="legacy_permissions",
        ),
        migrations.AlterField(
            model_name="profile",
            name="port_guard_pattern",
            field=models.CharField(
                blank=True,
                help_text="Регулярное выражение, совпадение которого с описанием порта будет запрещать изменять его статус и менять описание",
                max_length=500,
                null=True,
                verbose_name="Защитный RegExp для описания порта",
            ),
        ),
    ]
