import django.db.models.deletion
from django.db import migrations, models


def get_unique_device_name(Devices, name: str, bras_id: int) -> str:
    """Вернуть уникальное имя оборудования для переносимого BRAS."""
    base_name = name or f"BRAS {bras_id}"
    candidate = base_name
    counter = 1

    while Devices.objects.filter(name=candidate).exists():
        suffix = f" BRAS {bras_id}-{counter}"
        candidate = f"{base_name[:100 - len(suffix)]}{suffix}"
        counter += 1

    return candidate


def migrate_bras_to_devices(apps, schema_editor) -> None:
    """Связать BRAS с существующими устройствами или создать недостающие."""
    AuthGroup = apps.get_model("check", "AuthGroup")
    Bras = apps.get_model("check", "Bras")
    DeviceGroup = apps.get_model("check", "DeviceGroup")
    Devices = apps.get_model("check", "Devices")

    bras_group = DeviceGroup.objects.filter(name="BRAS").first()
    if bras_group is None:
        bras_group = DeviceGroup.objects.create(name="BRAS")

    for bras in Bras.objects.all():
        device = Devices.objects.filter(ip=bras.ip).first()
        if device is None:
            auth_group = AuthGroup.objects.create(
                name=f"BRAS {bras.name}",
                login=bras.login,
                password=bras.password,
                secret=bras.secret,
            )
            device = Devices.objects.create(
                name=get_unique_device_name(Devices, bras.name, bras.pk),
                ip=bras.ip,
                group=bras_group,
                auth_group=auth_group,
                cmd_protocol="ssh",
                port_scan_protocol="ssh",
                connection_pool_size=bras.connection_pool_size,
            )

        bras.device_id = device.pk
        bras.save(update_fields=["device"])


def restore_bras_fields(apps, schema_editor) -> None:
    """Восстановить старые поля BRAS из связанных устройств при откате."""
    Bras = apps.get_model("check", "Bras")

    for bras in Bras.objects.select_related("device"):
        device = bras.device
        bras.name = device.name[:10]
        bras.ip = device.ip
        bras.login = device.auth_group.login
        bras.password = device.auth_group.password
        bras.secret = device.auth_group.secret
        bras.connection_pool_size = device.connection_pool_size
        bras.save(
            update_fields=[
                "name",
                "ip",
                "login",
                "password",
                "secret",
                "connection_pool_size",
            ]
        )


class Migration(migrations.Migration):
    dependencies = [
        ("check", "0041_deviceinterfacepatternrule"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bras",
            name="name",
            field=models.CharField(max_length=10, null=True, verbose_name="Название"),
        ),
        migrations.AlterField(
            model_name="bras",
            name="ip",
            field=models.GenericIPAddressField(
                null=True,
                protocol="ipv4",
                unique=True,
                verbose_name="IP адрес",
            ),
        ),
        migrations.AlterField(
            model_name="bras",
            name="login",
            field=models.CharField(max_length=64, null=True, verbose_name="Логин"),
        ),
        migrations.AlterField(
            model_name="bras",
            name="password",
            field=models.CharField(max_length=64, null=True, verbose_name="Пароль"),
        ),
        migrations.AddField(
            model_name="bras",
            name="device",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="bras",
                to="check.devices",
                verbose_name="Оборудование",
            ),
        ),
        migrations.RunPython(migrate_bras_to_devices, restore_bras_fields),
        migrations.AlterField(
            model_name="bras",
            name="device",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="bras",
                to="check.devices",
                verbose_name="Оборудование",
            ),
        ),
        migrations.RemoveField(model_name="bras", name="connection_pool_size"),
        migrations.RemoveField(model_name="bras", name="ip"),
        migrations.RemoveField(model_name="bras", name="login"),
        migrations.RemoveField(model_name="bras", name="name"),
        migrations.RemoveField(model_name="bras", name="password"),
        migrations.RemoveField(model_name="bras", name="secret"),
        migrations.AlterModelOptions(
            name="bras",
            options={
                "ordering": ("device__name",),
                "verbose_name": "BRAS",
                "verbose_name_plural": "BRASes",
            },
        ),
        migrations.AddConstraint(
            model_name="bras",
            constraint=models.UniqueConstraint(
                fields=("device",),
                name="unique_bras_device",
            ),
        ),
    ]
