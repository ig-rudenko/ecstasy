import subprocess
from re import findall, IGNORECASE

from .vendors.base.types import InterfaceListType, InterfaceType


def physical_interface(name: str) -> bool:
    """
    Смотрит, относится ли интерфейс к физическим по указанным именам

    Не учитываются:
      VLAN, Loop, Null, Meth, System

    Также DSL каналы:
      dsl_channel

    Телефонные линии:
      pstn

    """

    name = name.lower()
    if findall(r"802\.1Q|loop|null|meth|vlan|sys|dsl_channel|pstn|bits", name, IGNORECASE):
        return False
    return True


def get_interfaces(device_ip, community, snmp_port=161) -> InterfaceListType:
    """

    С помощью snmpwalk смотрит состояние интерфейсов, имена, описания

    Текущее рабочее состояние интерфейса. (Oper Status)

    Состояние тестирования (testing) указывает на то, что рабочие пакеты не могут
    быть переданы.

    Если Admin Status (down), то Oper Status должен быть (down).

    Если Admin Status изменен на (up), то Oper Status должен измениться на (up),
    если интерфейс готов к передаче и приему сетевого трафика;

    Режим ожидания (dormant), если интерфейс ожидает внешних действий
    (например, последовательная линия, ожидающая входящего соединения);

    Порт будет оставаться в состоянии (down), если и только если есть ошибка,
    которая мешает ему перейти в состояние (up);

    Состояние (notPresent), если интерфейс имеет отсутствующие компоненты
    (как правило, аппаратные).

    :param device_ip: IP адрес оборудования
    :param community: SNMP Community
    :param snmp_port: SNMP порт (по умолчанию 161)
    :return: [('name', 'admin status', 'oper status', 'desc'), ...]
    """

    snmp_result: dict = {
        "IF-MIB::ifAlias": {},
        "IF-MIB::ifIndex": {},
        "IF-MIB::ifName": {},
        "IF-MIB::ifAdminStatus": {},
        "IF-MIB::ifOperStatus": {},
        "IF-MIB::ifDescr": {},
    }

    def snmpget(community, ip, port, mib) -> None:
        # Выполнение команды `snmpwalk -Oq -v2c -c <community> <ip>:<port> <mib>` и возврат результата.
        res = subprocess.run(
            ["snmpwalk", "-Oq", "-v2c", "-c", community, f"{ip}:{port}", mib],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            encoding="utf-8",
            errors="ignore",
            check=False,
        )
        # Он разбивает вывод команды на строки.
        for line in res.stdout.split("\n"):
            if not line:
                continue  # Пропускаем пустую строку
            res_line = findall(r"(\S+) (.*)", line)
            snmp_result[mib][res_line[0][0].replace(f"{mib}.", "")] = res_line[0][1]

    for key in snmp_result:
        snmpget(community, device_ip, snmp_port, key)

    # Убираем возможное переполнение в отрицательных индексах
    for k, v in snmp_result["IF-MIB::ifIndex"].items():
        try:
            v_int = int(v)
            if v_int < 0:
                # Если значение отрицательное, то прибавляем к нему 2^32, чтобы изменить знак на положительный
                snmp_result["IF-MIB::ifIndex"][k] = str(v_int + 2**32)
        except ValueError:
            continue

    result: InterfaceListType = []

    for snmp_index in snmp_result["IF-MIB::ifIndex"]:
        port_name = (
            snmp_result["IF-MIB::ifName"].get(snmp_index) or snmp_result["IF-MIB::ifDescr"][snmp_index]
        )

        if not physical_interface(port_name):
            continue

        oper_status = snmp_result["IF-MIB::ifOperStatus"].get(snmp_index, "")
        admin_status = snmp_result["IF-MIB::ifAdminStatus"].get(snmp_index, "")

        status: InterfaceType = "notPresent"
        if admin_status == "down":
            status = "admin down"
        elif oper_status in {"up", "down", "dormant"}:
            status = snmp_result["IF-MIB::ifOperStatus"][snmp_index]

        result.append(
            (
                port_name,
                status,
                snmp_result["IF-MIB::ifAlias"].get(snmp_index, ""),
            )
        )
    return result
