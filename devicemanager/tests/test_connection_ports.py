from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from devicemanager.dc import DeviceRemoteConnector, SimpleAuthObject, SSHSpawn
from devicemanager.device_connector.factory import DeviceSessionFactory
from devicemanager.remote.connector import RemoteDevice


class DeviceConnectionPortsTests(SimpleTestCase):
    """Tests for custom device connection ports."""

    def test_remote_device_sends_connection_ports_to_device_connector(self):
        """RemoteDevice includes custom protocol ports in connector payload."""

        auth = SimpleAuthObject(login="user", password="password")
        device = RemoteDevice(
            ip="192.0.2.10",
            auth_obj=auth,
            cmd_protocol="ssh",
            port_scan_protocol="snmp",
            snmp_community="public",
            make_session_global=True,
            telnet_port=2323,
            ssh_port=2222,
            snmp_port=1161,
        )
        response = Mock(status_code=200, headers={"Content-Type": "application/json"})
        response.json.return_value = {"data": []}
        device._remote_connector_address = "http://connector"
        device._session = Mock()
        device._session.post.return_value = response

        device.get_interfaces()

        payload = device._session.post.call_args.kwargs["json"]["connection"]
        self.assertEqual(payload["telnet_port"], 2323)
        self.assertEqual(payload["ssh_port"], 2222)
        self.assertEqual(payload["snmp_port"], 1161)

    def test_remote_device_uses_default_connection_ports(self):
        """RemoteDevice falls back to protocol defaults when ports are absent."""

        auth = SimpleAuthObject(login="user", password="password")
        device = RemoteDevice(
            ip="192.0.2.10",
            auth_obj=auth,
            cmd_protocol="ssh",
            port_scan_protocol="snmp",
            snmp_community="public",
            make_session_global=True,
        )
        response = Mock(status_code=200, headers={"Content-Type": "application/json"})
        response.json.return_value = {"data": []}
        device._remote_connector_address = "http://connector"
        device._session = Mock()
        device._session.post.return_value = response

        device.get_interfaces()

        payload = device._session.post.call_args.kwargs["json"]["connection"]
        self.assertEqual(payload["telnet_port"], 23)
        self.assertEqual(payload["ssh_port"], 22)
        self.assertEqual(payload["snmp_port"], 161)

    @patch("devicemanager.device_connector.factory.snmp.get_interfaces")
    def test_device_session_factory_passes_snmp_port_to_snmp_interfaces(self, get_interfaces):
        """DeviceSessionFactory uses custom SNMP port for SNMP interface scans."""

        get_interfaces.return_value = []
        factory = DeviceSessionFactory(
            ip="192.0.2.10",
            protocol="telnet",
            auth_obj=SimpleAuthObject(login="user", password="password"),
            make_session_global=True,
            pool_size=1,
            snmp_community="public",
            port_scan_protocol="snmp",
            snmp_port=1161,
        )

        factory.perform_method("get_interfaces")

        get_interfaces.assert_called_once_with(
            device_ip="192.0.2.10",
            community="public",
            snmp_port=1161,
        )

    def test_ssh_spawn_uses_custom_port(self):
        """SSH spawn command uses configured SSH port."""

        spawn = SSHSpawn(ip="192.0.2.10", login="user", port=2222)

        self.assertIn("ssh -p 2222 user@192.0.2.10", spawn.get_spawn_string())

    @patch("devicemanager.dc.DeviceMultiFactory.get_device")
    def test_device_remote_connector_passes_snmp_port_to_device_factory(self, get_device):
        """DeviceRemoteConnector passes SNMP port to detected device instance."""

        session = Mock()
        get_device.return_value = Mock()
        connector = DeviceRemoteConnector(
            ip="192.0.2.10",
            protocol="telnet",
            snmp_community="public",
            auth_obj=SimpleAuthObject(login="user", password="password"),
            snmp_port=1161,
        )

        with patch.object(connector, "_connect_by_telnet", return_value=session):
            connector.get_session()

        self.assertEqual(get_device.call_args.kwargs["snmp_port"], 1161)
