from threading import Barrier, Lock, Thread
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from devicemanager.device.zabbix_api import ThreadLocalZabbixAPIConnector
from devicemanager.remote.connector import PoolController


class ThreadLocalConnectorTests(SimpleTestCase):
    """Tests for HTTP clients shared by threaded Gunicorn workers."""

    def test_pool_controller_uses_separate_session_per_thread(self):
        """Each thread reuses its own requests session."""

        controller = PoolController()
        barrier = Barrier(2)
        results = []
        results_lock = Lock()

        def get_sessions():
            first_session = controller._get_session()
            barrier.wait(timeout=1)
            second_session = controller._get_session()
            with results_lock:
                results.append((first_session, second_session))

        with patch("devicemanager.remote.connector.requests.Session", side_effect=[Mock(), Mock()]):
            threads = [Thread(target=get_sessions), Thread(target=get_sessions)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=1)

        self.assertEqual(len(results), 2)
        self.assertIs(results[0][0], results[0][1])
        self.assertIs(results[1][0], results[1][1])
        self.assertIsNot(results[0][0], results[1][0])

    def test_zabbix_proxy_uses_separate_connector_per_thread(self):
        """Each thread reuses its own Zabbix connector."""

        connector_factory = Mock(side_effect=[Mock(), Mock()])
        proxy = ThreadLocalZabbixAPIConnector(connector_factory=connector_factory)
        barrier = Barrier(2)
        results = []
        results_lock = Lock()

        def get_connectors():
            first_connector = proxy._get_connector()
            barrier.wait(timeout=1)
            second_connector = proxy._get_connector()
            with results_lock:
                results.append((first_connector, second_connector))

        threads = [Thread(target=get_connectors), Thread(target=get_connectors)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=1)

        self.assertEqual(len(results), 2)
        self.assertIs(results[0][0], results[0][1])
        self.assertIs(results[1][0], results[1][1])
        self.assertIsNot(results[0][0], results[1][0])
