from datetime import datetime

from pyzabbix.api import ZabbixAPI


def get_group_problems(zbx_session: ZabbixAPI, zabbix_group_name: str) -> list[dict]:
    """
    Эта функция возвращает список проблем для данной группы хостов Zabbix, если она существует.

    :param zbx_session: Сессия Zabbix API.
    :param zabbix_group_name: Строка, представляющая имя группы Zabbix.
    """
    group: list = zbx_session.hostgroup.get(filter={"name": zabbix_group_name})
    if not group:  # Если такая группа НЕ существует.
        return []

    zabbix_group_id = group[0]["groupid"]

    hosts_id = [
        host["hostid"]
        # Получение всех хостов на мониторинге в группе с заданным идентификатором.
        for host in zbx_session.host.get(
            groupids=[zabbix_group_id], output=["hostid"], filter={"status": "0"}
        )
    ]

    # Получение проблемы узла сети из Zabbix.
    hosts_problems_list = zbx_session.problem.get(
        hostids=hosts_id,
        selectAcknowledges="extend",
        output="extend",
        filter={"name": "Оборудование недоступно"},
    )

    # Перебор списка проблем.
    return [get_host_acknowledges(zbx_session, problem) for problem in hosts_problems_list]


def get_host_acknowledges(zbx_session: ZabbixAPI, problem: dict) -> dict:
    """
    Эта функция извлекает подтверждения для данного сетевого узла с проблемой.

    :param zbx_session: Сессия Zabbix API.
    :param problem: Словарь, содержащий информацию о проблеме в сетевом узле
    :return: Словарь, содержащий идентификатор сетевого узла с проблемой и
     список подтверждений (если есть) для этой проблемы.
    """
    # ID узла сети, у которого проблема.

    host = zbx_session.item.get(triggerids=[problem["objectid"]], output=["hostid", "name"])

    acknowledges = [
        [
            ack["message"],
            datetime.fromtimestamp(int(ack["clock"])).strftime("%H:%M %d-%m-%Y"),
        ]
        for ack in problem["acknowledges"]
    ]

    return {"id": host[0]["hostid"], "acknowledges": acknowledges}
