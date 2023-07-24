import os
import re
from typing import Literal, Type, Union, Tuple

import requests

from .exceptions import InvalidMethod, RemoteAuthenticationFailed
from devicemanager import exceptions
from devicemanager.vendors.base.device import AbstractDevice
from devicemanager.vendors.base.types import (
    T_MACList,
    T_InterfaceVLANList,
    T_InterfaceList,
    T_MACTable,
)


class RemoteDevice(AbstractDevice):
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

    def _handle_error(self, error: dict):
        if hasattr(exceptions, error["type"]):
            SomeException: Type[exceptions.BaseDeviceException] = getattr(exceptions, error["type"])
            raise SomeException(error["message"], ip=self.ip)
        else:
            raise exceptions.DeviceException(error["message"], ip=self.ip)

    def _remote_call(self, method: str, **params):
        url = f"{self._remote_connector_address}/connector/{self.ip}/{method}"
        resp = requests.post(
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
            headers={
                "Token": os.getenv("DEVICE_CONNECTOR_TOKEN", ""),
            },
            timeout=60 * 10,
        )
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
            file_name_match = re.findall(
                r"filename=\"(\S+)\"", resp.headers.get("Content-Disposition")
            )
            file_name = file_name_match[0] if file_name_match else "file_name"
            return resp.content, file_name

        if resp.headers.get("Content-Type") == "application/json":
            return resp.json().get("data")

    def get_system_info(self):
        return self._remote_call("get_system_info")

    def get_interfaces(self) -> T_InterfaceList:
        return self._remote_call("get_interfaces")

    def get_vlans(self) -> T_InterfaceVLANList:
        return self._remote_call("get_vlans")

    def get_mac(self, port: str) -> T_MACList:
        return self._remote_call("get_mac", port=port)

    def reload_port(self, port: str, save_config=True) -> str:
        return self._remote_call("reload_port", port=port, save_config=True)

    def set_port(self, port: str, status: Literal["up", "down"], save_config=True) -> str:
        return self._remote_call("set_port", port=port, status=status, save_config=True)

    def save_config(self):
        return self._remote_call("save_config")

    def set_description(self, port: str, desc: str) -> str:
        return self._remote_call("set_description", port=port, desc=desc)

    def get_port_info(self, port: str) -> dict:
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

    def get_current_configuration(self) -> Tuple[Union[str, bytes], str]:
        return self._remote_call("get_current_configuration")

    def set_poe_out(self, port: str, status: str):
        return self._remote_call("set_poe_out", port=port, status=status)

    def change_profile(self, port: str, port_index: int):
        return self._remote_call("change_profile", port=port, port_index=port_index)

    def get_access_user_data(self, mac: str) -> str:
        return self._remote_call("get_access_user_data", mac=mac)

    def cut_access_user_session(self, mac: str):
        return self._remote_call("cut_access_user_session", mac=mac)

    def search_ip(self, ip_address: str) -> list:
        return self._remote_call("search_ip", ip_address=ip_address)

    def search_mac(self, mac_address: str) -> list:
        return self._remote_call("search_mac", mac_address=mac_address)

    def normalize_interface_name(self, intf: str) -> str:
        return self._remote_call("normalize_interface_name", intf=intf)

    def get_mac_table(self) -> T_MACTable:
        return self._remote_call("get_mac_table")
