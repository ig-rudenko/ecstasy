import subprocess
from re import findall, IGNORECASE
from typing import Tuple, List
from concurrent.futures import ThreadPoolExecutor


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
    if findall(
        r"802\.1Q|loop|null|meth|vlan|sys|dsl_channel|pstn|bits", name, IGNORECASE
    ):
        return False
    return True


def show_interfaces(
    device_ip, community, snmp_port=161
) -> List[Tuple[str, str, str, str]]:
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

    snmp_result = {
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
        )
        # Он разбивает вывод команды на строки.
        for line in res.stdout.split("\n"):
            if not line:
                continue  # Пропускаем пустую строку
            res_line = findall(r"(\S+) (.*)", line)
            snmp_result[mib][res_line[0][0].replace(f"{mib}.", "")] = res_line[0][1]

    with ThreadPoolExecutor() as snmp_executor:
        for key in snmp_result:
            snmp_executor.submit(snmpget, community, device_ip, snmp_port, key)
    result = []

    for snmp_index in snmp_result["IF-MIB::ifIndex"]:
        result.append(
            (
                snmp_result["IF-MIB::ifName"].get(snmp_index)
                or snmp_result["IF-MIB::ifDescr"][snmp_index],
                snmp_result["IF-MIB::ifAdminStatus"].get(snmp_index) or "-",
                snmp_result["IF-MIB::ifOperStatus"].get(snmp_index) or "-",
                snmp_result["IF-MIB::ifAlias"].get(snmp_index) or "",
            )
        )
    return result
