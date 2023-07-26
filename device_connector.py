import io
import logging
import os
import pathlib
from typing import TypedDict

from flask import Flask, after_this_request
from flask import request, jsonify, send_file

from devicemanager.dc import DeviceFactory, SimpleAuthObject
from devicemanager import snmp
from devicemanager.exceptions import BaseDeviceException


app = Flask(__name__)
TOKEN = os.getenv("DEVICE_CONNECTOR_TOKEN")
app.logger.setLevel(logging.INFO)


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


@app.route("/connector/<ip>/<method>", methods=["POST"])
def connector(ip: str, method: str):
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

    data = request.get_json(force=True)
    connection: ConnectionType = data.get("connection")
    print(ip, method, data)

    try:
        with DeviceFactory(
            ip=ip,
            protocol=connection.get("cmd_protocol"),
            auth_obj=SimpleAuthObject(**data.get("auth")),
            make_session_global=connection.get("make_session_global", True),
            pool_size=connection.get("pool_size", 3),
            snmp_community=connection.get("snmp_community"),
        ) as session:

            if method == "get_interfaces" and connection.get("port_scan_protocol") == "snmp":
                return jsonify(
                    {
                        "data": snmp.get_interfaces(
                            device_ip=ip, community=connection.get("snmp_community")
                        )
                    }
                )
            app.logger.info(f"{ip} {method}, {session.__class__.__name__}")
            if hasattr(session, method):
                session_method = getattr(session, method)
                params = data.get("params", {})
                method_data = session_method(**params)

                return handle_method_data(method_data)

            else:
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9999, use_reloader=True)
