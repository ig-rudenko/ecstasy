from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from .models import AuthGroup, DeviceGroup, Devices


class DevicesResource(resources.ModelResource):
    auth_group = fields.Field(
        column_name="auth_group",
        attribute="auth_group",
        widget=ForeignKeyWidget(AuthGroup, "name"),  # noqa
    )
    group = fields.Field(
        column_name="group",
        attribute="group",
        widget=ForeignKeyWidget(DeviceGroup, "name"),  # noqa
    )

    class Meta:
        model = Devices
        import_id_fields = ("ip",)
        fields = (
            "ip",
            "name",
            "active",
            "vendor",
            "model",
            "serial_number",
            "os_version",
            "snmp_community",
            "auth_group",
            "group",
            "connection_pool_size",
            "port_scan_protocol",
            "cmd_protocol",
        )
        export_order = (
            "ip",
            "name",
            "active",
            "vendor",
            "model",
            "serial_number",
            "os_version",
            "snmp_community",
            "auth_group",
            "group",
            "connection_pool_size",
            "port_scan_protocol",
            "cmd_protocol",
        )
