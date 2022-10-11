from django.db import models


class SingletonModel(models.Model):
    """ Singleton Django Model """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Save object to the database. Removes all other entries if there
        are any.
        """
        self.__class__.objects.exclude(id=self.id).delete()
        super(SingletonModel, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        """
        Load object from the database. Failing that, create a new empty
        (default) instance of the object and return it (without saving it
        to the database).
        """
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()


class LogsElasticStackSettings(SingletonModel):
    """
    Настройки для отображения логов в Elastic Stack (Singleton)
    """
    kibana_url = models.CharField(
        null=True, blank=True,
        max_length=100, verbose_name="Kibana discover URL", help_text="Например: http://kibana:5601/app/discover#/"
    )
    time_range = models.CharField(
        null=True, blank=True,
        max_length=4, verbose_name="Глубина временного диапазона", help_text="Например: 1d, 24h или 30m"
    )
    output_columns = models.CharField(
        null=True, blank=True,
        max_length=255, verbose_name='Колонки',
        help_text="Поля через запятую, которые должны отображаться как колонки.<br> Например: message,host.ip"
    )

    QUERY_LANGS = (
        ('KQL', 'KQL'),
        ('Lucene', 'Lucene')
    )
    query_lang = models.CharField(
        null=True, blank=True,
        choices=QUERY_LANGS, max_length=10, verbose_name="Язык запросов", default='KQL',
        help_text='<a target="_blank" href="https://www.elastic.co/guide/en/kibana/8.4/kuery-query.html">'
                  'Documentation</a>'
    )
    query_str = models.CharField(
        null=True, blank=True,
        max_length=255, verbose_name="Строка для поиска",
        help_text="Необходимо указать, как будет произведен поиск логов для отдельного устройства.<br>"
                  "Доступны следующие переменные:<br>"
                  "{device.ip}<br>"
                  "{device.name}<br>"
                  "{device.vendor}<br>"
                  "{device.model}<br>"
                  "Пример строки: host.ip : {device.ip}"
    )
    time_field = models.CharField(
        null=True, blank=True,
        max_length=100, verbose_name="timestamp поле", help_text="Сортировка будет происходить по нему.<br>"
                                                                 "Например: @timestamp"
    )

    def __str__(self):
        return "Elastic Stack settings"

    def is_set(self):
        """ Проверяет, настройки имеются или нет """
        return self.kibana_url and self.time_range and self.time_field and self.query_str

    class Meta:
        db_table = 'elastic_settings'
        verbose_name = verbose_name_plural = 'Elastic Stack settings'


class ZabbixConfig(SingletonModel):
    """ Настройки для подключения к Zabbix через http """

    url = models.URLField(verbose_name="URL", help_text="Например: https://10.0.0.1/zabbix")
    login = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    def __str__(self):
        return "Zabbix settings"

    class Meta:
        db_table = 'zabbix_api_settings'
        verbose_name = verbose_name_plural = 'Zabbix API settings'


class VlanTracerouteConfig(SingletonModel):
    """ Настройки для работы vlan traceroute """

    vlan_start = models.TextField(
        verbose_name="Имя оборудования для начала трассировки",
        help_text="Разделять необходимо запятой, если требуется указать несколько"
    )
    find_device_pattern = models.TextField(
        verbose_name="Регулярное выражение",
        help_text="Используется для того, "
                  "чтобы найти в описании порта имя другого оборудования и продолжить трассировку"
    )

    def __str__(self):
        return "VLAN traceroute settings"

    class Meta:
        db_table = 'vlan_traceroute_settings'
        verbose_name = verbose_name_plural = 'VLAN traceroute settings'
