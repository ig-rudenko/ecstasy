import io
import logging
import os
import pathlib
from typing import TypedDict

from flask import Flask, after_this_request
from flask import request, jsonify, send_file

from devicemanager.dc import SimpleAuthObject
from devicemanager.device_connector.exceptions import MethodError
from devicemanager.device_connector.factory import DeviceSessionFactory
from devicemanager.exceptions import BaseDeviceException
from devicemanager.session_control import DEVICE_SESSIONS

app = Flask(__name__)
TOKEN = os.getenv("DEVICE_CONNECTOR_TOKEN", "ASDIH!hausd17391")
app.logger.setLevel(logging.DEBUG)


class ConnectionType(TypedDict):
    cmd_protocol: str
    port_scan_protocol: str
    snmp_community: str
    pool_size: int
    make_session_global: bool


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


def check_token():
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


@app.route("/connector/<ip>/<method>", methods=["POST"])
def connector(ip: str, method: str):
    token_error = check_token()
    if token_error:
        return token_error

    data = request.get_json(force=True)
    connection: ConnectionType = data.get("connection")
    print(ip, method)

    try:
        factory = DeviceSessionFactory(
            ip=ip,
            protocol=connection.get("cmd_protocol", "ssh"),
            auth_obj=SimpleAuthObject(**data.get("auth")),
            make_session_global=connection.get("make_session_global", True),
            pool_size=connection.get("pool_size", None),
            snmp_community=connection.get("snmp_community", ""),
            port_scan_protocol=connection.get("port_scan_protocol", "ssh"),
        )
        params = data.get("params", {})

        try:
            data = factory.perform_method(method, **params)
            return handle_method_data(data)

        except MethodError:
            resp = jsonify({"error": "no attr"})
            resp.status_code = 400
            return resp

    except (BaseDeviceException, Exception) as err:
        app.logger.error(err.__class__.__name__, exc_info=err)
        resp = jsonify(
            {
                "type": err.__class__.__name__,
                "message": str(err),
            }
        )
        resp.status_code = 500
        return resp


@app.route("/pool/<ip>", methods=["DELETE"])
def delete_connection_pool(ip: str):
    """Очистить пул соединений"""
    token_error = check_token()
    if token_error:
        return token_error
    DEVICE_SESSIONS.delete_pool(ip)
    resp = jsonify({"message": "Connection pool deleted"})
    resp.status_code = 204
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, use_reloader=True)
