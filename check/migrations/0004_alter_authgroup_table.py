# Generated by Django 4.0.6 on 2022-07-27 07:38

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("check", "0003_authgroup_alter_devicegroup_table_and_more"),
    ]

    operations = [
        migrations.AlterModelTable(
            name="authgroup",
            table="device_auth_groups",
        ),
    ]
