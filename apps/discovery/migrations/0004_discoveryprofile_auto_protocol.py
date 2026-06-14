from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("discovery", "0003_reset_orphaned_created_candidates"),
    ]

    operations = [
        migrations.AlterField(
            model_name="discoveryprofile",
            name="cmd_protocol",
            field=models.CharField(
                choices=[
                    ("auto", "Авто (SSH → Telnet)"),
                    ("telnet", "telnet"),
                    ("ssh", "ssh"),
                ],
                default="ssh",
                max_length=6,
                verbose_name="Протокол выполнения команд",
            ),
        ),
        migrations.AlterField(
            model_name="discoveryprofile",
            name="port_scan_protocol",
            field=models.CharField(
                choices=[
                    ("auto", "Авто (SSH → Telnet)"),
                    ("snmp", "snmp"),
                    ("telnet", "telnet"),
                    ("ssh", "ssh"),
                ],
                default="snmp",
                max_length=6,
                verbose_name="Протокол сбора интерфейсов",
            ),
        ),
    ]
