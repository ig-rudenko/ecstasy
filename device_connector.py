import io
import logging
import os
import pathlib
from ipaddress import IPv4Address
from typing import NotRequired, TypedDict, cast

from flask import Flask, Response, after_this_request, jsonify, request, send_file
from ping3 import ping

from devicemanager.dc import SimpleAuthObject
from devicemanager.device_connector.connection_status import CONNECTION_STATUSES
from devicemanager.device_connector.exceptions import MethodError
from devicemanager.device_connector.factory import DeviceSessionFactory
from devicemanager.exceptions import BaseDeviceException
from devicemanager.session_control import DEVICE_SESSIONS

app = Flask(__name__)
TOKEN = os.getenv("DEVICE_CONNECTOR_TOKEN", "ASDIH!hausd17391")
app.logger.setLevel(os.getenv("DEVICE_CONNECTOR_LOG_LEVEL", logging.INFO))


class ConnectionType(TypedDict):
    cmd_protocol: str
    port_scan_protocol: str
    snmp_community: str
    pool_size: int
    make_session_global: bool
    telnet_port: NotRequired[int]
    ssh_port: NotRequired[int]
    snmp_port: NotRequired[int]


def handle_method_data(data):
    if isinstance(data, pathlib.Path):

        @after_this_request
        def remove_file(response):
            try:
                data.unlink()
            except Exception as error:
                app.logger.error("Error removing or closing downloaded file handle", error)
            return response

        return send_file(data, download_name=data.name)

    if isinstance(data, io.BytesIO):
        return send_file(data, download_name="file")

    return jsonify({"data": data})


def check_token() -> Response | None:
    request_token = request.headers.get("Token")
    if not request_token or request_token != TOKEN:
        resp = jsonify(
            {
                "type": "AuthenticationFailed",
                "message": "Неверный токен доступа к DeviceConnector",
            }
        )
        resp.status_code = 401
        return resp
    return None


@app.route("/connector/<ip>/<method>", methods=["POST"])
def connector(ip: str, method: str):
    token_error = check_token()
    if token_error is not None:
        return token_error

    try:
        valid_ip = IPv4Address(ip).compressed
    except ValueError:
        resp = jsonify({"error": "invalid ip"})
        resp.status_code = 400
        return resp

    data = request.get_json(force=True)
    connection = cast(ConnectionType, data.get("connection") or {})

    try:
        factory = DeviceSessionFactory(
            ip=valid_ip,
            protocol=connection.get("cmd_protocol", "ssh"),
            auth_obj=SimpleAuthObject(**data.get("auth")),
            make_session_global=connection.get("make_session_global", True),
            pool_size=connection.get("pool_size", None),
            snmp_community=connection.get("snmp_community", ""),
            port_scan_protocol=connection.get("port_scan_protocol", "ssh"),
            telnet_port=connection.get("telnet_port"),
            ssh_port=connection.get("ssh_port"),
            snmp_port=connection.get("snmp_port"),
        )
        params = data.get("params", {})

        try:
            data = factory.perform_method(method, **params)
            if not (method == "get_interfaces" and factory.port_scan_protocol == "snmp"):
                CONNECTION_STATUSES.record_success(valid_ip)
            return handle_method_data(data)

        except MethodError:
            resp = jsonify({"error": "no attr"})
            resp.status_code = 400
            return resp

    except (BaseDeviceException, Exception) as err:
        CONNECTION_STATUSES.record_error(
            valid_ip,
            err,
            ssh_port=factory.ssh_port if "factory" in locals() else 22,
        )
        app.logger.error(err.__class__.__name__, exc_info=err)
        resp = jsonify(
            {
                "type": err.__class__.__name__,
                "message": str(err),
            }
        )
        resp.status_code = 500
        return resp


@app.route("/pool/<ip>", methods=["GET", "DELETE"])
def delete_connection_pool(ip: str):
    """Очистить пул соединений"""
    token_error = check_token()
    if token_error:
        return token_error

    try:
        valid_ip = IPv4Address(ip).compressed
    except ValueError:
        resp = jsonify({"error": "invalid ip"})
        resp.status_code = 400
        return resp

    if request.method == "DELETE":
        DEVICE_SESSIONS.delete_pool(valid_ip)
        resp = jsonify({"message": "Connection pool deleted"})
        resp.status_code = 204
        return resp

    statuses = DEVICE_SESSIONS.get_pool_status(valid_ip)
    return jsonify({"statuses": statuses, **CONNECTION_STATUSES.get_status(valid_ip)})


@app.post("/ssh-host-key/<ip>")
def confirm_ssh_host_key(ip: str):
    """Confirm a previously scanned SSH host key change."""

    token_error = check_token()
    if token_error:
        return token_error

    try:
        valid_ip = IPv4Address(ip).compressed
    except ValueError:
        resp = jsonify({"error": "invalid ip"})
        resp.status_code = 400
        return resp

    try:
        confirmed = CONNECTION_STATUSES.confirm_ssh_host_key(valid_ip)
    except Exception as err:
        app.logger.error("SSH host key confirmation failed", exc_info=err)
        resp = jsonify({"error": "ssh host key confirmation failed"})
        resp.status_code = 500
        return resp

    if not confirmed:
        resp = jsonify({"error": "no pending ssh host key change"})
        resp.status_code = 409
        return resp

    DEVICE_SESSIONS.delete_pool(valid_ip)
    return Response(status=204)


@app.route("/ping/<ip>", methods=["POST"])
def ping_pong_device(ip: str):
    token_error = check_token()
    if token_error:
        return token_error

    p = ping(ip, timeout=2)
    return jsonify({"available": isinstance(p, float)})


if __name__ == "__main__":
    app.run(
        host=os.getenv("DEVICE_CONNECTOR_BIND_HOST", "0.0.0.0"),
        port=int(os.getenv("DEVICE_CONNECTOR_BIND_PORT", 8000)),
    )
