import os
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from devicemanager.dc import DeviceRemoteConnector, SimpleAuthObject, SSHSpawn
from devicemanager.device_connector.factory import DeviceSessionFactory
from devicemanager.exceptions import SSHConnectionError
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
            pool_expired_seconds=2,
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

    @patch("devicemanager.dc.SSHKnownHostsStore")
    def test_ssh_spawn_uses_warning_fallback_when_keyscan_fails(self, known_hosts_store):
        """Automatic acceptance falls back to the fingerprint printed by OpenSSH."""

        store = known_hosts_store.return_value
        spawn = SSHSpawn(ip="192.0.2.10", login="user", port=2222)
        ssh_output = "The fingerprint for the ED25519 key sent by the remote host is\n" "SHA256:new."

        spawn.accept_changed_host_key(ssh_output)

        store.accept_changed.assert_called_once()
        self.assertEqual(store.accept_changed.call_args.args[:2], ("192.0.2.10", 2222))
        self.assertEqual(store.accept_changed.call_args.args[3], ssh_output)

    def test_ssh_spawn_uses_first_offered_cipher(self):
        """SSH spawn передает один шифр, а не несовместимый список."""

        spawn = SSHSpawn(ip="192.0.2.10", login="user")

        with patch("devicemanager.dc.subprocess.run") as run:
            run.return_value = Mock(
                stdout="aes128-cbc\n3des-cbc\ndes-cbc\n",
                returncode=0,
            )
            spawn.get_ciphers("Their offer: aes128-cbc,3des-cbc,des-cbc")

        self.assertEqual(spawn.ciphers, "aes128-cbc")
        self.assertIn("-c aes128-cbc", spawn.get_spawn_string())

    @patch("devicemanager.dc.subprocess.run")
    def test_ssh_spawn_skips_host_key_algorithms_unsupported_by_local_client(self, run):
        """SSH spawn выбирает первый предложенный алгоритм, доступный локальному OpenSSH."""

        run.return_value = Mock(stdout="rsa-sha2-256\nssh-ed25519\n", returncode=0)
        spawn = SSHSpawn(ip="192.0.2.10", login="user")

        spawn.get_host_key_algorithms("Their offer: ssh-dss,rsa-sha2-256")

        self.assertEqual(spawn.host_key_algorithms, "rsa-sha2-256")
        self.assertIn("-oHostKeyAlgorithms=+rsa-sha2-256", spawn.get_spawn_string())

    @patch("devicemanager.dc.subprocess.run")
    def test_ssh_spawn_adds_supported_mac_algorithm(self, run):
        """SSH spawn поддерживает согласование устаревшего MAC алгоритма."""

        run.return_value = Mock(stdout="hmac-sha1\nhmac-sha2-256\n", returncode=0)
        spawn = SSHSpawn(ip="192.0.2.10", login="user")

        spawn.get_macs("Their offer: hmac-md5,hmac-sha1")

        self.assertEqual(spawn.macs, "hmac-sha1")
        self.assertIn("-oMACs=+hmac-sha1", spawn.get_spawn_string())

    @patch("devicemanager.dc.subprocess.run")
    @patch("devicemanager.dc.SSHSpawn.get_session")
    def test_ssh_connector_retries_with_supported_mac_algorithm(self, get_session, run):
        """SSH connector повторяет подключение с MAC из предложения сервера."""

        run.return_value = Mock(stdout="hmac-sha1\nhmac-sha2-256\n", returncode=0)
        failed_session = Mock()
        failed_session.expect.side_effect = [12, 0]
        failed_session.before = b"Their offer: hmac-md5,hmac-sha1\r\n"
        connected_session = Mock()
        connected_session.expect.return_value = 5
        get_session.side_effect = [failed_session, connected_session]
        connector = DeviceRemoteConnector(
            ip="192.0.2.10",
            protocol="ssh",
            snmp_community="public",
            auth_obj=SimpleAuthObject(login="user", password="password"),
        )

        session = connector._connect_by_ssh()

        self.assertIs(session, connected_session)
        self.assertEqual(get_session.call_count, 2)

    @patch("devicemanager.dc.subprocess.run")
    @patch("devicemanager.dc.SSHSpawn.get_session")
    def test_ssh_connector_does_not_retry_with_unsupported_host_key_algorithm(
        self,
        get_session,
        run,
    ):
        """SSH connector не запускает команду с неподдерживаемым host key алгоритмом."""

        run.return_value = Mock(stdout="rsa-sha2-256\nssh-ed25519\n", returncode=0)
        session = Mock()
        session.expect.side_effect = [1, 0]
        session.before = b"Their offer: ssh-dss\r\n"
        session.isalive.return_value = False
        get_session.return_value = session
        connector = DeviceRemoteConnector(
            ip="192.0.2.10",
            protocol="ssh",
            snmp_community="public",
            auth_obj=SimpleAuthObject(login="user", password="password"),
        )

        with self.assertRaises(SSHConnectionError):
            connector._connect_by_ssh()

        get_session.assert_called_once()

    @patch("devicemanager.dc.SSHSpawn.get_session")
    def test_ssh_connector_stops_when_negotiation_offer_cannot_be_parsed(self, get_session):
        """Нераспознанный ответ OpenSSH не запускает бесконечный цикл подключения."""

        session = Mock()
        session.expect.side_effect = [2, 0]
        session.before = b" type 'aes128-cbc,3des-cbc,des-cbc'\r\n"
        session.isalive.return_value = False
        get_session.return_value = session
        connector = DeviceRemoteConnector(
            ip="192.0.2.10",
            protocol="ssh",
            snmp_community="public",
            auth_obj=SimpleAuthObject(login="user", password="password"),
        )

        with self.assertRaises(SSHConnectionError):
            connector.get_session()

        get_session.assert_called_once()

    @patch.dict(os.environ, {"DEVICE_CONNECTOR_AUTO_ACCEPT_CHANGED_SSH_HOST_KEY": "1"})
    @patch("devicemanager.dc.SSHSpawn.accept_changed_host_key")
    @patch("devicemanager.dc.SSHSpawn.get_session")
    def test_ssh_connector_accepts_changed_host_key_and_retries_connection(
        self,
        get_session,
        accept_changed_host_key,
    ):
        """Автопринятие ключа повторяет handshake и возвращает сессию в первом вызове."""

        changed_key_session = Mock()
        changed_key_session.expect.return_value = 11
        changed_key_session.isalive.return_value = False
        changed_key_session.before = b"SHA256:new"
        changed_key_session.after = b"HOST IDENTIFICATION HAS CHANGED"
        connected_session = Mock()
        connected_session.expect.side_effect = [3, 5]
        get_session.side_effect = [changed_key_session, connected_session]
        connector = DeviceRemoteConnector(
            ip="192.0.2.10",
            protocol="ssh",
            snmp_community="public",
            auth_obj=SimpleAuthObject(login="user", password="password"),
            ssh_port=2222,
        )

        session = connector._connect_by_ssh()

        self.assertIs(session, connected_session)
        accept_changed_host_key.assert_called_once()
        self.assertIn("HOST IDENTIFICATION HAS CHANGED", accept_changed_host_key.call_args.args[0])
        connected_session.sendline.assert_called_once_with("yes")
        self.assertEqual(get_session.call_count, 2)

    @patch.dict(os.environ, {"DEVICE_CONNECTOR_AUTO_ACCEPT_CHANGED_SSH_HOST_KEY": "0"})
    @patch("devicemanager.dc.SSHSpawn.accept_changed_host_key")
    @patch("devicemanager.dc.SSHSpawn.get_session")
    def test_ssh_connector_keeps_manual_confirmation_when_auto_accept_is_disabled(
        self,
        get_session,
        accept_changed_host_key,
    ):
        """Без флага изменившийся ключ по-прежнему требует ручного подтверждения."""

        changed_key_session = Mock()
        changed_key_session.expect.return_value = 11
        changed_key_session.isalive.return_value = False
        changed_key_session.before = b"SHA256:new"
        changed_key_session.after = b"HOST IDENTIFICATION HAS CHANGED"
        get_session.return_value = changed_key_session
        connector = DeviceRemoteConnector(
            ip="192.0.2.10",
            protocol="ssh",
            snmp_community="public",
            auth_obj=SimpleAuthObject(login="user", password="password"),
        )

        with self.assertRaisesMessage(SSHConnectionError, "SSH HOST IDENTIFICATION HAS CHANGED") as context:
            connector._connect_by_ssh()

        self.assertIn("SHA256:new", context.exception.ssh_output)
        accept_changed_host_key.assert_not_called()
        get_session.assert_called_once()

    @patch.dict(os.environ, {"DEVICE_CONNECTOR_AUTO_ACCEPT_CHANGED_SSH_HOST_KEY": "1"})
    @patch("devicemanager.dc.SSHSpawn.accept_changed_host_key", side_effect=RuntimeError("write failed"))
    @patch("devicemanager.dc.SSHSpawn.get_session")
    def test_ssh_connector_keeps_changed_key_error_when_auto_accept_fails(
        self,
        get_session,
        accept_changed_host_key,
    ):
        """Ошибка записи ключа сохраняет ручный сценарий подтверждения."""

        changed_key_session = Mock()
        changed_key_session.expect.return_value = 11
        changed_key_session.isalive.return_value = False
        changed_key_session.before = b"SHA256:new"
        changed_key_session.after = b"HOST IDENTIFICATION HAS CHANGED"
        get_session.return_value = changed_key_session
        connector = DeviceRemoteConnector(
            ip="192.0.2.10",
            protocol="ssh",
            snmp_community="public",
            auth_obj=SimpleAuthObject(login="user", password="password"),
        )

        with self.assertRaisesMessage(SSHConnectionError, "SSH HOST IDENTIFICATION HAS CHANGED"):
            connector._connect_by_ssh()

        accept_changed_host_key.assert_called_once()
        get_session.assert_called_once()

    @patch("devicemanager.dc.DeviceMultiFactory.get_device")
    def test_device_remote_connector_passes_snmp_port_to_device_factory(self, get_device):
        """DeviceRemoteConnector passes SNMP port to detected device instance."""

        session = Mock()
        detected_device = Mock()
        get_device.return_value = detected_device
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
        self.assertEqual(detected_device.connection_protocol, "telnet")
