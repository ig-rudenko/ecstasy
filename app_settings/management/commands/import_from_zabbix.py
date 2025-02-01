import re
from functools import lru_cache
from typing import TypedDict

from django.core.management.base import BaseCommand

from app_settings.models import ZabbixConfig
from check.models import DeviceGroup, Devices, AuthGroup
from devicemanager.device.zabbix_api import ZabbixAPIConnector


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @classmethod
    def disable(cls):
        cls.HEADER = ""
        cls.OKBLUE = ""
        cls.OKCYAN = ""
        cls.OKGREEN = ""
        cls.WARNING = ""
        cls.FAIL = ""
        cls.ENDC = ""
        cls.BOLD = ""
        cls.UNDERLINE = ""


class ZabbixInterfaceType(TypedDict):
    ip: str


class ZabbixGroupType(TypedDict):
    groupid: str
    name: str


class ZabbixHostType(TypedDict):
    hostid: str
    host: str
    name: str
    status: str
    description: str
    groups: list[ZabbixGroupType]
    interfaces: list[ZabbixInterfaceType]


class Command(BaseCommand):
    help = "Импорт узлов сети из zabbix"

    @staticmethod
    def get_zabbix_connector(url: str = "", login: str = "", password: str = ""):
        db_zabbix_config = ZabbixConfig.load()
        db_zabbix_config.url = url or db_zabbix_config.url
        db_zabbix_config.login = login or db_zabbix_config.login
        db_zabbix_config.password = password or db_zabbix_config.password

        zbx_connector = ZabbixAPIConnector()
        zbx_connector.set(db_zabbix_config)
        return zbx_connector

    @staticmethod
    @lru_cache()
    def get_auth_group(name: str):
        try:
            print("Группа авторизации:", name)
            return AuthGroup.objects.get(name=name)
        except AuthGroup.DoesNotExist:
            print("Не найдена группа авторизации:", name)
            exit(1)

    @lru_cache()
    def get_model_group(self, name: str):
        return DeviceGroup.objects.get_or_create(name=name)[0]

    @staticmethod
    def get_hosts(zbx, group_name) -> list[ZabbixHostType]:
        groups = zbx.hostgroup.get(filter={"name": group_name}, output=["groupid"])
        if groups:
            print("Найдена группа:", group_name, "->", groups)
            hosts: list[ZabbixHostType] = zbx.host.get(
                groupids=[g["groupid"] for g in groups],
                output=["hostid", "host", "name", "status", "description"],
                selectGroups=["groupid", "name"],
                selectInterfaces=["ip"],
                sortfield=["name"],
            )
            print("Найдено узлов:", len(hosts))
            return hosts
        return []

    @staticmethod
    def get_host_ip(host: ZabbixHostType) -> str:
        host_ip = ""
        for interface in host["interfaces"]:
            if interface["ip"] not in ["127.0.0.1", "0.0.0.0"]:
                host_ip = interface["ip"]
        return host_ip

    @staticmethod
    def host_is_valid(host: ZabbixHostType, name_pattern: str, ip_pattern: str) -> bool:
        if name_pattern and not re.search(name_pattern, host["name"]):
            return False

        if ip_pattern:
            for interface in host["interfaces"]:
                if not re.search(ip_pattern, interface["ip"]):
                    return False

        return True

    def import_host(
        self,
        host: ZabbixHostType,
        *,
        group: DeviceGroup,
        interface_scan: str,
        cli_protocol: str,
        auth_group: AuthGroup,
        snmp_community: str | None,
        save: bool,
        debug: bool = False,
    ):
        host_ip = self.get_host_ip(host)
        text = (
            f'Узел сети: "{Colors.HEADER}{host["name"]}{Colors.ENDC}" '
            f'IP: "{Colors.BOLD}{host_ip}"{Colors.ENDC} '
            f"Группа: {group} Авторизация: {auth_group}"
        )

        if debug:
            text += " | " + str(host)

        if not host_ip:
            print(f"{Colors.FAIL}Не найден уникальный IP{Colors.ENDC}: {host['interfaces']}", text)
            return

        if Devices.objects.filter(ip=host_ip).exists():
            if debug:
                print(f"{Colors.OKCYAN}Такой IP уже есть в базе: {host_ip} {Colors.ENDC}| {text}")
            return

        if not save:
            print(f"{Colors.OKGREEN}Новый{Colors.ENDC}", text)
            return

        Devices.objects.create(
            ip=host_ip,
            name=host["name"],
            group=group,
            auth_group=auth_group,
            port_scan_protocol=interface_scan,
            cmd_protocol=cli_protocol,
            snmp_community=snmp_community,
        )
        print(f"{Colors.OKBLUE}Добавлен{Colors.ENDC}", text)

    def handle(self, *args, **options):
        print("Начало импорта узлов сети\n")
        if options["no_color"]:
            Colors.disable()

        zbx_connector = self.get_zabbix_connector(
            url=options["server"], login=options["user"], password=options["password"]
        )
        print(
            "Будут использованы следующие параметры подключения к Zabbix:",
            f"  url       {zbx_connector.zabbix_url}",
            f"  user      {zbx_connector.zabbix_user}",
            f"  password  {'*'*len(zbx_connector.zabbix_password)}",
            sep="\n",
        )

        groups = options["groups"].split(",")
        print("\nИмпортируем группы:", groups)
        auth_group = self.get_auth_group(options["auth"])

        with zbx_connector.connect() as zbx:
            for group_name in groups:
                hosts = self.get_hosts(zbx, group_name)

                model_group_name = options["change_group"] or group_name
                group = self.get_model_group(model_group_name)

                for host in hosts:
                    if not self.host_is_valid(host, options["name_pattern"], options["ip_pattern"]):
                        # Пропускаем узлы, которые не соответствуют условиям.
                        if options["debug"]:
                            print(f"{Colors.FAIL}Узел сети с неправильным форматом: {host} {Colors.ENDC}")
                        continue

                    if not options["all_status"] and host["status"] == "1":
                        # Пропускаем узлы с деактивированным статусом.
                        if options["debug"]:
                            print(f"{Colors.FAIL}Узел сети с деактивированным статусом: {host} {Colors.ENDC}")
                        continue

                    self.import_host(
                        host,
                        group=group,
                        interface_scan=options["interface_scan"],
                        cli_protocol=options["cli_protocol"],
                        auth_group=auth_group,
                        save=options["save"],
                        debug=options["debug"],
                        snmp_community=options["snmp_community"],
                    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-g",
            "--groups",
            type=str,
            help="Имена Zabbix групп через запятую",
            required=True,
        )

        parser.add_argument(
            "-a",
            "--auth",
            type=str,
            help="Имя группы авторизации для узла сети",
            required=True,
        )

        parser.add_argument(
            "-s",
            "--save",
            action="store_true",
            help="Сохранить в базу узлы сети",
        )

        parser.add_argument(
            "--change-group",
            type=str,
            help="Имя группы Ecstasy, которая будет использоваться для всех узлов сети. "
            "Если не указана, то будет использована оригинальная группа Zabbix",
        )

        parser.add_argument(
            "--all-status",
            action="store_true",
            help="Импортируем также узлы сети, которые деактивированы в Zabbix",
        )

        parser.add_argument(
            "--interface-scan",
            type=str,
            choices=["telnet", "ssh", "snmp"],
            default="ssh",
            help="Протокол для сбора интерфейсов узла сети. (по умолчанию ssh)",
        )

        parser.add_argument(
            "--snmp-community",
            type=str,
            help="SNMP Community (необязательно)",
        )

        parser.add_argument(
            "--cli-protocol",
            type=str,
            choices=["telnet", "ssh"],
            default="ssh",
            help="Протокол для выполнения команд узла сети. (по умолчанию ssh)",
        )

        parser.add_argument(
            "--name-pattern",
            type=str,
            help="Паттерн для имени узлов сети. Если совпадает, то будет импортирован. (необязательно)",
            default="",
        )

        parser.add_argument(
            "--ip-pattern",
            type=str,
            help="Паттерн для IP узла сети. Если совпадает, то будет импортирован. (необязательно)",
            default="",
        )

        parser.add_argument(
            "--server",
            type=str,
            help="URL сервера Zabbix (необязательно)",
            default="",
        )
        parser.add_argument(
            "--user",
            type=str,
            help="Имя пользователя Zabbix (необязательно)",
            default="",
        )
        parser.add_argument(
            "--password",
            type=str,
            help="Пароль пользователя Zabbix (необязательно)",
            default="",
        )

        parser.add_argument(
            "--debug",
            action="store_true",
            help="Выводить дополнительную информацию",
        )
