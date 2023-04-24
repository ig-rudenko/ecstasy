# Generated by Django 4.0.7 on 2022-08-29 08:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("check", "0015_alter_devices_ip_alter_devices_model_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="authgroup",
            options={
                "ordering": ("id",),
                "verbose_name": "Auth group",
                "verbose_name_plural": "Auth groups",
            },
        ),
        migrations.RemoveField(
            model_name="devices",
            name="protocol",
        ),
        migrations.AddField(
            model_name="devices",
            name="cmd_protocol",
            field=models.CharField(
                choices=[("telnet", "telnet"), ("ssh", "ssh")],
                default="telnet",
                help_text="Выберите протокол, с помощью которого будет осуществляться подключение для вызова команд (например: поиск MAC адресов или сброс порта)",
                max_length=6,
                verbose_name="Протокол для выполнения команд",
            ),
        ),
        migrations.AddField(
            model_name="devices",
            name="port_scan_protocol",
            field=models.CharField(
                choices=[("snmp", "snmp"), ("telnet", "telnet"), ("ssh", "ssh")],
                default="telnet",
                help_text="Выберите протокол, с помощью которого будет осуществляться сканирование интерфейсов",
                max_length=6,
                verbose_name="Протокол для поиска интерфейсов",
            ),
        ),
        migrations.AlterField(
            model_name="devices",
            name="auth_group",
            field=models.ForeignKey(
                help_text="Указываем группу, для удаленного подключения к оборудованию. Используется для протоколов telnet и ssh. Если на оборудовании логин/пароль из указанной группы не подошли, то будут автоматически подбираться пары логин/пароль по очереди, указанной в этом списке (кроме неверного)",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="check.authgroup",
                verbose_name="Группа авторизации",
            ),
        ),
        migrations.AlterField(
            model_name="devices",
            name="snmp_community",
            field=models.CharField(
                blank=True,
                help_text="Версия - v2c. Используется для сбора интерфейсов, если указан протокол - SNMP",
                max_length=64,
                null=True,
                verbose_name="SNMP community",
            ),
        ),
    ]