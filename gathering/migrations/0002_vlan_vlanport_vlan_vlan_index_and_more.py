# Generated by Django 5.1.5 on 2025-02-04 19:55

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("check", "0031_devices_collect_vlan_info"),
        ("gathering", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Vlan",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "vlan",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(4096),
                        ]
                    ),
                ),
                ("vlan_desc", models.CharField(max_length=50)),
                ("datetime", models.DateTimeField(auto_now=True)),
                (
                    "device",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="check.devices"),
                ),
            ],
            options={
                "db_table": "vlans",
            },
        ),
        migrations.CreateModel(
            name="VlanPort",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("port", models.CharField(max_length=50)),
                ("desc_port", models.CharField(blank=True, max_length=128, null=True)),
                (
                    "vlan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ports",
                        to="gathering.vlan",
                    ),
                ),
            ],
            options={
                "db_table": "vlans_ports",
            },
        ),
        migrations.AddIndex(
            model_name="vlan",
            index=models.Index(fields=["vlan"], name="vlan_index"),
        ),
        migrations.AlterUniqueTogether(
            name="vlan",
            unique_together={("vlan", "device")},
        ),
        migrations.AlterUniqueTogether(
            name="vlanport",
            unique_together={("vlan", "port")},
        ),
    ]
