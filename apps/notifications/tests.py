from unittest.mock import patch

from django.db import connection
from django.test import SimpleTestCase

from apps.notifications.apps import get_notification_trigger_bulk_create_kwargs


class NotificationTriggerBulkCreateKwargsTests(SimpleTestCase):
    def test_with_update_conflicts_target_support(self):
        """Ensure unique_fields is included when backend supports explicit conflict target."""
        with patch.object(connection.features, "supports_update_conflicts_with_target", True):
            kwargs = get_notification_trigger_bulk_create_kwargs()

        self.assertEqual(kwargs["update_fields"], ["description"])
        self.assertTrue(kwargs["update_conflicts"])
        self.assertEqual(kwargs["unique_fields"], ["name"])

    def test_without_update_conflicts_target_support(self):
        """Ensure unique_fields is omitted when backend does not support explicit conflict target."""
        with patch.object(connection.features, "supports_update_conflicts_with_target", False):
            kwargs = get_notification_trigger_bulk_create_kwargs()

        self.assertEqual(kwargs["update_fields"], ["description"])
        self.assertTrue(kwargs["update_conflicts"])
        self.assertNotIn("unique_fields", kwargs)
