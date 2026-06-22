from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from apps.check.models import AuthGroup, DeviceGroup, Devices
from apps.maps.admin.admin_forms import LayerFrom
from apps.maps.models import Layers, Maps
from apps.maps.services.maps import get_map_layers_geo_data


class DeviceGroupLayerTestCase(TestCase):
    """Tests for map layers built from equipment groups."""

    @patch("apps.maps.admin.admin_forms.get_zabbix_groups")
    def test_layer_form_allows_empty_zabbix_group(self, get_zabbix_groups_mock):
        """Zabbix group selector keeps an explicit empty option for non-Zabbix layers."""
        get_zabbix_groups_mock.return_value = (("zabbix-group", "zabbix-group"),)

        form = LayerFrom()

        self.assertEqual(form.fields["zabbix_group_name"].choices[0], ("", "---------"))

    def test_map_render_includes_devices_from_selected_device_group(self):
        """Device group layer returns only devices from the selected group with coordinates."""
        device_group = DeviceGroup.objects.create(name="Access")
        other_group = DeviceGroup.objects.create(name="Core")
        auth_group = AuthGroup.objects.create(name="test", login="test", password="test")
        device = Devices.objects.create(
            ip="10.0.0.1",
            name="sw-1",
            group=device_group,
            auth_group=auth_group,
            latitude=Decimal("44.123456"),
            longitude=Decimal("33.654321"),
            vendor="Eltex",
            model="MES",
            serial_number="SN123",
            os_version="1.0",
        )
        Devices.objects.create(
            ip="10.0.0.2",
            name="sw-no-coords",
            group=device_group,
            auth_group=auth_group,
        )
        Devices.objects.create(
            ip="10.0.0.3",
            name="core-1",
            group=other_group,
            auth_group=auth_group,
            latitude=Decimal("45.000000"),
            longitude=Decimal("34.000000"),
        )
        layer = Layers.objects.create(
            name="Access devices",
            device_group=device_group,
            points_color="#112233",
            points_border_color="#445566",
            points_size=24,
            marker_icon_name="square",
        )
        map_object = Maps.objects.create(name="Network map")
        map_object.layers.add(layer)

        layers_data = get_map_layers_geo_data(map_object)

        self.assertEqual(len(layers_data), 1)
        self.assertEqual(layers_data[0]["name"], "Access devices")
        self.assertEqual(layers_data[0]["type"], "geojson")
        features = layers_data[0]["features"]["features"]
        self.assertEqual(len(features), 1)
        self.assertEqual(
            features[0],
            {
                "type": "Feature",
                "id": device.id,
                "geometry": {
                    "type": "Point",
                    "coordinates": [33.654321, 44.123456],
                },
                "properties": {
                    "name": "sw-1",
                    "group": "Access",
                    "iconName": "square",
                    "marker-color": "#112233",
                    "device": {
                        "name": "sw-1",
                        "ip": "10.0.0.1",
                        "group": "Access",
                        "url": "/device/sw-1",
                        "vendor": "Eltex",
                        "model": "MES",
                        "serialNumber": "SN123",
                        "osVersion": "1.0",
                    },
                },
            },
        )
        self.assertEqual(layers_data[0]["properties"]["Marker"]["Size"], 24)
