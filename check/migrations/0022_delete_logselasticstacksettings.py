# Generated by Django 4.0.7 on 2022-10-04 10:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("check", "0021_logselasticstacksettings_alter_usersactions_options"),
    ]

    operations = [
        migrations.DeleteModel(
            name="LogsElasticStackSettings",
        ),
    ]