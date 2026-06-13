from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class TracerouteConfigMigrationTest(TransactionTestCase):
    """Проверка переименования настроек трассировки без потери данных."""

    migrate_from = ("app_settings", "0004_accessringsettings")
    migrate_to = (
        "app_settings",
        "0005_tracerouteconfig_delete_vlantracerouteconfig",
    )

    def setUp(self) -> None:
        """Подготовить базу в состоянии до проверяемой миграции."""
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        self.old_apps = executor.loader.project_state([self.migrate_from]).apps

    def tearDown(self) -> None:
        """Вернуть базу к актуальному состоянию миграций."""
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_migration_preserves_traceroute_settings(self):
        """Миграция должна переименовать модель, таблицу и поля без потери данных."""
        VlanTracerouteConfig = self.old_apps.get_model(
            "app_settings",
            "VlanTracerouteConfig",
        )
        old_config = VlanTracerouteConfig.objects.create(
            vlan_start="switch-1\nswitch-2",
            vlan_start_regex=r"^switch-\d+$",
            ip_pattern=r"^192\.0\.2\.",
            find_device_pattern=r"neighbor: (\S+)",
            cache_timeout=900,
        )

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        apps = executor.loader.project_state([self.migrate_to]).apps
        TracerouteConfig = apps.get_model("app_settings", "TracerouteConfig")

        config = TracerouteConfig.objects.get()
        self.assertEqual(config.pk, old_config.pk)
        self.assertEqual(config.start_device, "switch-1\nswitch-2")
        self.assertEqual(config.start_device_regex, r"^switch-\d+$")
        self.assertEqual(config.device_ip_pattern, r"^192\.0\.2\.")
        self.assertEqual(config.find_device_pattern, r"neighbor: (\S+)")
        self.assertEqual(config.cache_timeout, 900)
