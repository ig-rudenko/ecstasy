from import_export import resources

from .models import DescNameFormat, VlanName


class VlanNameResource(resources.ModelResource):
    class Meta:
        model = VlanName
        import_id_fields = ("vid",)
        fields = ("vid", "name", "description")
        export_order = fields


class DescNameFormatResource(resources.ModelResource):
    class Meta:
        model = DescNameFormat
        import_id_fields = ("standard",)
        fields = ("standard", "replacement")
        export_order = fields
