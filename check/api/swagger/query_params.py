from rest_framework import serializers


class DeviceInterfacesQueryParamsSerializer(serializers.Serializer):
    current_status = serializers.BooleanField(default=False)
    vlans = serializers.BooleanField(default=False)
    add_links = serializers.BooleanField(default=True)
    add_comments = serializers.BooleanField(default=True)
    add_zabbix_graph = serializers.BooleanField(default=True)


class DeviceQueryParamsSerializer(serializers.Serializer):
    return_fields = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        label="Какие поля возвращать, если не указано, то все",
    )
    ip = serializers.IPAddressField(required=False, label="IP адрес")
    name = serializers.CharField(required=False, label="Название")
    group = serializers.CharField(required=False, label="Группа")
    vendor = serializers.CharField(required=False, label="Производитель")
    model = serializers.CharField(required=False, label="Модель")
    serial_number = serializers.CharField(required=False, label="Серийный номер")
    os_version = serializers.CharField(required=False, label="Версия ОС")
    port_scan_protocol = serializers.ChoiceField(
        required=False, choices=["telnet", "ssh", "snmp"], label="Протокол для сканирования портов"
    )
    cmd_protocol = serializers.ChoiceField(
        required=False, choices=["telnet", "ssh"], label="Протокол для выполнения команд"
    )
    active = serializers.BooleanField(
        required=False,
        label="Активно ли оборудование",
    )
    collect_interfaces = serializers.BooleanField(
        required=False,
        label="Собираются ли интерфейсы на оборудовании периодической задачей `interfaces_scan`",
    )
    collect_mac_addresses = serializers.BooleanField(
        required=False,
        label="Собираются ли MAC адреса на оборудовании периодической задачей `mac_table_gather_task`",
    )
    collect_vlan_info = serializers.BooleanField(
        required=False,
        label="Собираются ли интерфейсы с VLAN на оборудовании периодической задачей `vlan_table_gather_task`",
    )
    collect_configurations = serializers.BooleanField(
        required=False,
        label="Собирается ли конфигурация оборудования периодической задачей `configuration_gather_task`",
    )
    connection_pool_size = serializers.IntegerField(
        required=False,
        label="Количество подключений к оборудованию, которые могут быть одновременно открыты",
        min_value=1,
        max_value=100,
    )
