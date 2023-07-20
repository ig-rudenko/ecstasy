import os
from typing import TypedDict

from flask import Flask
from flask import request, jsonify

from devicemanager.dc import DeviceFactory, SimpleAuthObject
from devicemanager import snmp
from devicemanager.exceptions import BaseDeviceException

app = Flask(__name__)
TOKEN = os.getenv("DEVICE_CONNECTOR_TOKEN")


class ConnectionType(TypedDict):
    cmd_protocol: str
    port_scan_protocol: str
    snmp_community: str
    pool_size: int


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

    try:
        with DeviceFactory(
            ip=ip,
            protocol=connection.get("cmd_protocol"),
            auth_obj=SimpleAuthObject(**data.get("auth")),
            make_session_global=data.get("make_session_global", True),
            pool_size=connection.get("pool_size", 3),
        ) as session:

            if method == "get_interfaces" and connection.get("port_scan_protocol") == "snmp":
                return jsonify(
                    {
                        "data": snmp.get_interfaces(
                            device_ip=ip, community=connection.get("snmp_community")
                        )
                    }
                )

            if hasattr(session, method):
                session_method = getattr(session, method)
                params = data.get("params", {})

                method_data = session_method(**params)
                return jsonify({"data": method_data})

            else:
                resp = jsonify({"error": "no attr"})
                resp.status_code = 400
                return resp

    except (BaseDeviceException, Exception) as err:
        resp = jsonify(
            {
                "type": err.__class__.__name__,
                "message": str(err),
            }
        )
        resp.status_code = 500
        return resp


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9999, use_reloader=True)
