# Generated by Django 4.0.7 on 2022-10-04 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LogsElasticStackSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kibana_url', models.CharField(blank=True, help_text='Например: http://kibana:5601/app/discover#/', max_length=100, null=True, verbose_name='Kibana discover URL')),
                ('time_range', models.CharField(blank=True, help_text='Например: 1d, 24h или 30m', max_length=4, null=True, verbose_name='Глубина временного диапазона')),
                ('output_columns', models.CharField(blank=True, help_text='Поля через запятую, которые должны отображаться как колонки.<br> Например: message,host.ip', max_length=255, null=True, verbose_name='Колонки')),
                ('query_lang', models.CharField(blank=True, choices=[('KQL', 'KQL'), ('Lucene', 'Lucene')], default='KQL', help_text='<a target="_blank" href="https://www.elastic.co/guide/en/kibana/8.4/kuery-query.html">Documentation</a>', max_length=10, null=True, verbose_name='Язык запросов')),
                ('query_str', models.CharField(blank=True, help_text='Необходимо указать, как будет произведен поиск логов для отдельного устройства.<br>Доступны следующие переменные:<br>{device.ip}<br>{device.name}<br>{device.vendor}<br>{device.model}<br>Пример строки: host.ip : {device.ip}', max_length=255, null=True, verbose_name='Строка для поиска')),
                ('time_field', models.CharField(blank=True, help_text='Сортировка будет происходить по нему.<br>Например: @timestamp', max_length=100, null=True, verbose_name='timestamp поле')),
            ],
            options={
                'verbose_name': 'Elastic Stack settings',
                'verbose_name_plural': 'Elastic Stack settings',
                'db_table': 'elastic_settings',
            },
        ),
        migrations.CreateModel(
            name='VlanTracerouteConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vlan_start', models.TextField(help_text='Разделять необходимо запятой, если требуется указать несколько', verbose_name='Имя оборудования для начала трассировки')),
                ('find_device_pattern', models.TextField(help_text='Используется для того, чтобы найти в описании порта имя другого оборудования и продолжить трассировку', verbose_name='Регулярное выражение')),
            ],
            options={
                'verbose_name': 'VLAN traceroute settings',
                'verbose_name_plural': 'VLAN traceroute settings',
                'db_table': 'vlan_traceroute_settings',
            },
        ),
        migrations.CreateModel(
            name='ZabbixConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(help_text='Например: https://10.0.0.1/zabbix', verbose_name='URL')),
                ('login', models.CharField(max_length=100)),
                ('password', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'Zabbix API settings',
                'verbose_name_plural': 'Zabbix API settings',
                'db_table': 'zabbix_api_settings',
            },
        ),
    ]
