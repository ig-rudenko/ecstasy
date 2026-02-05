import os
import re
from collections.abc import Sequence
from typing import Literal, Never

import requests

from devicemanager import exceptions
from devicemanager.device_connector.types import RemoteCommand
from devicemanager.vendors.base.device import (
    AbstractCableTestDevice,
    AbstractDevice,
    AbstractDSLProfileDevice,
    AbstractPOEDevice,
    AbstractSearchDevice,
    AbstractUserSessionsDevice,
)
from devicemanager.vendors.base.types import (
    ArpInfoResult,
    InterfaceListType,
    InterfaceVLANListType,
    MACListType,
    MACTableType,
    PortInfoType,
    SetDescriptionResult,
    SystemInfo,
)

from ..device_connector.factory import DEFAULT_POOL_SIZE
from .exceptions import InvalidMethod, RemoteAuthenticationFailed


class PoolController:

    def __init__(self):
        self._remote_connector_address = os.getenv("DEVICE_CONNECTOR_ADDRESS")
        self._session = requests.Session()
        self._session.headers.update({"Token": os.getenv("DEVICE_CONNECTOR_TOKEN", "")})

    def clear_pool(self, ip: str) -> bool:
        resp = self._session.delete(f"{self._remote_connector_address}/pool/{ip}", timeout=3)
        return resp.status_code == 204

    def get_pool_status(self, ip: str) -> list[bool]:
        resp = self._session.get(f"{self._remote_connector_address}/pool/{ip}", timeout=3)
        if resp.status_code != 200:
            return []
        return resp.json().get("statuses", [])


pool_controller = PoolController()


class RemoteDevice(
    AbstractDevice,
    AbstractSearchDevice,
    AbstractPOEDevice,
    AbstractCableTestDevice,
    AbstractDSLProfileDevice,
    AbstractUserSessionsDevice,
):
    def __init__(
        self,
        ip: str,
        auth_obj,
        cmd_protocol: str,
        port_scan_protocol: str,
        snmp_community: str,
        make_session_global: bool,
        pool_size: int = DEFAULT_POOL_SIZE,
    ):
        self.ip = ip
        self._remote_auth = {
            "login": auth_obj.login,
            "password": auth_obj.password,
            "secret": auth_obj.secret,
        }
        self._cmd_protocol = cmd_protocol
        self._port_scan_protocol = port_scan_protocol
        self._snmp_community = snmp_community
        self._make_session_global = make_session_global
        self._remote_connector_address = os.getenv("DEVICE_CONNECTOR_ADDRESS")
        self._pool_size = pool_size

        self._timeout = 60 * 3
        self._session = requests.Session()
        self._session.headers.update({"Token": os.getenv("DEVICE_CONNECTOR_TOKEN", "")})

    def _handle_error(self, error: dict) -> Never:
        self._delete_pool()  # Удаляем пул соединений, чтобы он создался заново
        if hasattr(exceptions, error["type"]):
            some_exception: type[exceptions.BaseDeviceException] = getattr(exceptions, error["type"])
            raise some_exception(error["message"], ip=self.ip)

        raise exceptions.DeviceException(error["message"], ip=self.ip)

    def _delete_pool(self):
        self._session.delete(f"{self._remote_connector_address}/pool/{self.ip}", timeout=3)

    def _remote_call(self, method: str, **params):
        url = f"{self._remote_connector_address}/connector/{self.ip}/{method}"
        try:
            resp = self._session.post(
                url=url,
                json={
                    "connection": {
                        "cmd_protocol": self._cmd_protocol,
                        "port_scan_protocol": self._port_scan_protocol,
                        "snmp_community": self._snmp_community,
                        "make_session_global": self._make_session_global,
                        "pool_size": self._pool_size,
                    },
                    "auth": self._remote_auth,
                    "params": params,
                },
                timeout=self._timeout,
            )
        except requests.exceptions.ConnectionError as exc:
            raise requests.exceptions.ConnectionError("Не удалось подключиться к DeviceConnector") from exc
        except requests.exceptions.Timeout as exc:
            raise requests.exceptions.ConnectTimeout("Время ожидания ответа от DeviceConnector") from exc
        except requests.exceptions.MissingSchema as exc:
            raise requests.exceptions.ConnectionError(
                "Неверный формат URL для подключения DeviceConnector"
            ) from exc

        if 200 <= resp.status_code <= 299:
            return self._handle_response(resp)
        if resp.status_code == 401:
            raise RemoteAuthenticationFailed(resp.json().get("message"), ip=self.ip)
        if 400 <= resp.status_code <= 499:
            raise InvalidMethod(f'Метод "{method}" отсутствует', ip=self.ip)
        return self._handle_error(resp.json())

    @staticmethod
    def _handle_response(resp: requests.Response):
        if "filename" in resp.headers.get("Content-Disposition", ""):
            file_name_match = re.findall(r"filename=(\S+)", resp.headers.get("Content-Disposition", ""))
            file_name = file_name_match[0] if file_name_match else "file_name"
            return resp.content, file_name

        if resp.headers.get("Content-Type") == "application/json":
            return resp.json().get("data")
        return resp.text

    def get_system_info(self) -> SystemInfo:
        return self._remote_call("get_system_info")

    def get_interfaces(self) -> InterfaceListType:
        return self._remote_call("get_interfaces")

    def get_vlans(self) -> InterfaceVLANListType:
        return self._remote_call("get_vlans")

    def get_mac(self, port: str) -> MACListType:
        return self._remote_call("get_mac", port=port)

    def reload_port(self, port: str, save_config=True) -> str:
        return self._remote_call("reload_port", port=port, save_config=save_config)

    def set_port(self, port: str, status: str, save_config=True) -> str:
        return self._remote_call("set_port", port=port, status=status, save_config=save_config)

    def save_config(self) -> str:
        return self._remote_call("save_config")

    def set_description(self, port: str, desc: str) -> SetDescriptionResult:  # type: ignore
        result = self._remote_call("set_description", port=port, desc=desc)
        return SetDescriptionResult(**result)

    def get_port_info(self, port: str) -> PortInfoType:
        return self._remote_call("get_port_info", port=port)

    def get_port_type(self, port: str) -> str:
        return self._remote_call("get_port_type", port=port)

    def get_port_config(self, port: str) -> str:
        return self._remote_call("get_port_config", port=port)

    def get_port_errors(self, port: str) -> str:
        return self._remote_call("get_port_errors", port=port)

    def get_device_info(self) -> dict:
        return self._remote_call("get_device_info")

    def virtual_cable_test(self, port: str) -> dict:
        return self._remote_call("virtual_cable_test", port=port)

    def get_current_configuration(self) -> tuple[str | bytes, str]:
        return self._remote_call("get_current_configuration")

    def set_poe_out(self, port: str, status: str):
        return self._remote_call("set_poe_out", port=port, status=status)

    def change_profile(self, port: str, profile_index: int) -> str:
        return self._remote_call("change_profile", port=port, profile_index=profile_index)

    def get_access_user_data(self, mac: str) -> str:
        return self._remote_call("get_access_user_data", mac=mac)

    def cut_access_user_session(self, mac: str):
        return self._remote_call("cut_access_user_session", mac=mac)

    def search_ip(self, ip_address: str) -> list[ArpInfoResult]:
        result = self._remote_call("search_ip", ip_address=ip_address)
        return [ArpInfoResult(*r) for r in result]

    def search_mac(self, mac_address: str) -> list[ArpInfoResult]:
        result = self._remote_call("search_mac", mac_address=mac_address)
        return [ArpInfoResult(*r) for r in result]

    def vlans_on_port(
        self,
        port: str,
        operation: Literal["add", "delete"],
        vlans: Sequence[int],
        tagged: bool = True,
    ) -> MACTableType:
        return self._remote_call("vlans_on_port", port=port, operation=operation, vlans=vlans, tagged=tagged)

    def execute_command(self, cmd: str) -> str:
        return self._remote_call("execute_command", cmd=cmd)

    def execute_commands_list(self, command_list: list[RemoteCommand]) -> list[str]:
        return self._remote_call("execute_commands_list", commands=command_list)
