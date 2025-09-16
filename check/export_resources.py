from import_export import fields, resources

from .models import Devices


class DevicesResource(resources.ModelResource):
    auth_group = fields.Field(column_name="auth_group")
    group = fields.Field(column_name="group")

    @staticmethod
    def dehydrate_auth_group(obj):
        return obj.auth_group.name

    @staticmethod
    def dehydrate_group(obj):
        return obj.group.name

    class Meta:
        model = Devices
        fields = (
            "ip",
            "name",
            "active",
            "vendor",
            "model",
            "serial_number",
            "auth_group",
            "group",
            "connection_pool_size",
        )
        export_order = (
            "ip",
            "name",
            "active",
            "vendor",
            "model",
            "serial_number",
            "auth_group",
            "group",
            "connection_pool_size",
        )
