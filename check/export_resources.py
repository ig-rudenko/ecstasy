from import_export import resources, fields

from .models import Devices


class DevicesResource(resources.ModelResource):
    auth_group = fields.Field(column_name="Группа авторизации")
    group = fields.Field(column_name="Группа")

    @staticmethod
    def dehydrate_auth_group(obj):
        return obj.auth_group.name

    @staticmethod
    def dehydrate_group(obj):
        return obj.group.name

    class Meta:
        model = Devices
        fields = ("ip", "name", "vendor", "model", "auth_group", "group")
        export_order = ("ip", "name", "vendor", "model", "auth_group", "group")
