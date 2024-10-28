"""
# Модели для сохранения настроек для взаимодействия Ecstasy с Zabbix, Elastic, VLAN Traceroute

Каждая модель представляет собой singleton, так как настройка должна быть только в единственном варианте

"""

from django.db import models


class SingletonModel(models.Model):
    """
    ## Singleton Django Model
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        ## Сохранение объекта в базе данных.

        Удаляет все остальные записи, если таковые имеются.
        """
        self.__class__.objects.exclude(id=self.id).delete()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """
        ## Загрузка объекта из базы данных.

        В противном случае создадим новый пустой (по умолчанию) экземпляр объекта
        и вернем его (без сохранения в базе данных).
        """
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()


class LogsElasticStackSettings(SingletonModel):
    """
    ## Настройки для отображения логов в Elastic Stack (Singleton)
    """

    kibana_url = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        verbose_name="Kibana discover URL",
        help_text="Например: http://kibana:5601/app/discover#/",
    )
    time_range = models.CharField(
        null=True,
        blank=True,
        max_length=4,
        verbose_name="Глубина временного диапазона",
        help_text="Например: 1d, 24h или 30m",
    )
    output_columns = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        verbose_name="Колонки",
        help_text="Поля через запятую, которые должны отображаться как колонки.<br> Например: message,host.ip",
    )

    QUERY_LANGS = (("kuery", "KQL"), ("lucene", "Lucene"))
    query_lang = models.CharField(
        null=True,
        blank=True,
        choices=QUERY_LANGS,
        max_length=10,
        verbose_name="Язык запросов",
        default="KQL",
        help_text='<a target="_blank" href="https://www.elastic.co/guide/en/kibana/8.4/kuery-query.html">'
        "Documentation</a>",
    )
    query_str = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        verbose_name="Строка для поиска",
        help_text="Необходимо указать, как будет произведен поиск логов для отдельного устройства.<br>"
        "Доступны следующие переменные:<br>"
        "{device.ip}<br>"
        "{device.name}<br>"
        "{device.vendor}<br>"
        "{device.model}<br>"
        "Пример строки: host.ip : {device.ip}",
    )
    time_field = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        verbose_name="timestamp поле",
        help_text="Сортировка будет происходить по нему.<br>" "Например: @timestamp",
    )

    def __str__(self):
        return "Elastic Stack settings"

    def is_set(self):
        """Проверяет, настройки имеются или нет"""
        return self.kibana_url and self.time_range and self.time_field and self.query_str

    def query_kibana_url(self, **kwargs) -> str:
        """
        ## Эта функция принимает словарь аргументов для форматирования строки query_str
         и возвращает URL для входа в Kibana
        """
        if self.is_set():
            query_str = self.query_str.format(**kwargs) if self.query_str else ""

            return (
                f"{self.kibana_url}?_g=(filters:!(),refreshInterval:(pause:!t,value:0),"
                f"time:(from:now-{self.time_range},to:now))"
                f"&_a=(columns:!({self.output_columns}),interval:auto,"
                f"query:(language:{self.query_lang},"
                f"query:'{query_str}'),"
                f"sort:!(!('{self.time_field}',desc)))"
            )

        return ""

    class Meta:
        db_table = "elastic_settings"
        verbose_name = verbose_name_plural = "Elastic Stack settings"


class ZabbixConfig(SingletonModel):
    """
    ## Настройки для подключения к Zabbix API через http
    """

    url = models.URLField(verbose_name="URL", help_text="Например: https://10.0.0.1/zabbix")
    login = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    def __str__(self):
        return "Zabbix settings"

    def save(self, *args, **kwargs):
        """
        После сохранения новых настроек Zabbix API в базу, необходимо указать эти параметры для `ZabbixAPIConnection`.
        """
        super().save(*args, **kwargs)
        # pylint: disable-next=import-outside-toplevel
        from devicemanager.device import zabbix_api

        zabbix_api.set(self)

    class Meta:
        db_table = "zabbix_api_settings"
        verbose_name = verbose_name_plural = "Zabbix API settings"


class VlanTracerouteConfig(SingletonModel):
    """
    ## Настройки для работы VLAN traceroute
    """

    vlan_start = models.TextField(
        verbose_name="Имя оборудования для начала трассировки",
        help_text="Разделять необходимо переносом строки, если требуется указать несколько",
        default="",
        null=True,
        blank=True,
    )
    vlan_start_regex = models.TextField(
        verbose_name="Регулярное выражение",
        help_text="Используется для того, чтобы найти оборудования, с которых начинается трассировка",
        default="",
        null=True,
        blank=True,
    )
    ip_pattern = models.TextField(
        verbose_name="Регулярное выражение для указания IP",
        help_text="Используется для того, чтобы найти оборудования, с которых начинается трассировка",
        default="",
        null=True,
        blank=True,
    )
    find_device_pattern = models.TextField(
        verbose_name="Регулярное выражение",
        help_text="Используется для того, "
        "чтобы найти в описании порта имя другого оборудования и продолжить трассировку",
    )
    cache_timeout = models.IntegerField(
        verbose_name="Время в секундах для кеширования",
        default=60 * 5,
    )

    def __str__(self):
        return "VLAN traceroute settings"

    class Meta:
        db_table = "vlan_traceroute_settings"
        verbose_name = verbose_name_plural = "VLAN traceroute settings"
