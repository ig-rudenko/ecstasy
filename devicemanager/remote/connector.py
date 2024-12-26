import os
import re
from typing import Literal, Type, Sequence

import requests

from devicemanager import exceptions
from devicemanager.vendors.base.device import (
    AbstractDevice,
    AbstractSearchDevice,
    AbstractPOEDevice,
    AbstractCableTestDevice,
    AbstractDSLProfileDevice,
    AbstractUserSessionsDevice,
)
from devicemanager.vendors.base.types import (
    MACListType,
    InterfaceVLANListType,
    InterfaceListType,
    MACTableType,
    SetDescriptionResult,
    ArpInfoResult,
    SystemInfo,
    PortInfoType,
)
from .exceptions import InvalidMethod, RemoteAuthenticationFailed


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

        self._timeout = 60 * 3
        self._session = requests.Session()
        self._session.headers.update({"Token": os.getenv("DEVICE_CONNECTOR_TOKEN", "")})

    def _handle_error(self, error: dict):
        self._delete_pool()  # Удаляем пул соединений, чтобы он создался заново
        if hasattr(exceptions, error["type"]):
            some_exception: Type[exceptions.BaseDeviceException] = getattr(exceptions, error["type"])
            raise some_exception(error["message"], ip=self.ip)
        else:
            raise exceptions.DeviceException(error["message"], ip=self.ip)

    def _delete_pool(self):
        self._session.delete(f"{self._remote_connector_address}/pool/{self.ip}")

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
                    },
                    "auth": self._remote_auth,
                    "params": params,
                },
                timeout=self._timeout,
            )
        except requests.exceptions.ConnectionError:
            raise requests.exceptions.ConnectionError(f"Не удалось подключиться к DeviceConnector")
        except requests.exceptions.Timeout:
            raise requests.exceptions.ConnectTimeout(f"Время ожидания ответа от DeviceConnector")

        if 200 <= resp.status_code <= 299:
            return self._handle_response(resp)
        elif resp.status_code == 401:
            raise RemoteAuthenticationFailed(resp.json().get("message"), ip=self.ip)
        elif 400 <= resp.status_code <= 499:
            raise InvalidMethod(f'Метод "{method}" отсутствует', ip=self.ip)
        elif resp.status_code >= 500:
            self._handle_error(resp.json())

    @staticmethod
    def _handle_response(resp):
        if "filename" in resp.headers.get("Content-Disposition", ""):
            file_name_match = re.findall(r"filename=(\S+)", resp.headers.get("Content-Disposition"))
            file_name = file_name_match[0] if file_name_match else "file_name"
            return resp.content, file_name

        if resp.headers.get("Content-Type") == "application/json":
            return resp.json().get("data")

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

    def change_profile(self, port: str, profile_index: int):
        return self._remote_call("change_profile", port=port, profile_index=profile_index)

    def get_access_user_data(self, mac: str) -> str:
        return self._remote_call("get_access_user_data", mac=mac)

    def cut_access_user_session(self, mac: str):
        return self._remote_call("cut_access_user_session", mac=mac)

    def search_ip(self, ip_address: str) -> list[ArpInfoResult]:
        result = self._remote_call("search_ip", ip_address=ip_address)
        return list(map(lambda r: ArpInfoResult(*r), result))

    def search_mac(self, mac_address: str) -> list[ArpInfoResult]:
        print(mac_address)
        result = self._remote_call("search_mac", mac_address=mac_address)
        return list(map(lambda r: ArpInfoResult(*r), result))

    def vlans_on_port(
        self,
        port: str,
        operation: Literal["add", "delete"],
        vlans: Sequence[int],
        tagged: bool = True,
    ) -> MACTableType:
        return self._remote_call("vlans_on_port", port=port, operation=operation, vlans=vlans, tagged=tagged)
