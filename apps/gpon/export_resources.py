from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from .models import Address, Customer, End3, Service, TechCapability


class CustomerResource(resources.ModelResource):
    class Meta:
        model = Customer
        import_id_fields = ("contract",)
        fields = (
            "type",
            "company_name",
            "first_name",
            "surname",
            "last_name",
            "phone",
            "contract",
        )
        export_order = fields


class AddressResource(resources.ModelResource):
    class Meta:
        model = Address
        import_id_fields = ("id",)
        fields = (
            "id",
            "region",
            "settlement",
            "plan_structure",
            "street",
            "house",
            "block",
            "floor",
            "apartment",
        )
        export_order = fields


class ServiceResource(resources.ModelResource):
    class Meta:
        model = Service
        import_id_fields = ("id",)
        fields = ("id", "name")
        export_order = fields


class End3Resource(resources.ModelResource):
    address = fields.Field(
        column_name="address",
        attribute="address",
        widget=ForeignKeyWidget(Address, "id"),  # noqa
    )

    class Meta:
        model = End3
        import_id_fields = ("id",)
        fields = ("id", "address", "location", "type", "capacity")
        export_order = fields


class TechCapabilityResource(resources.ModelResource):
    end3 = fields.Field(
        column_name="end3",
        attribute="end3",
        widget=ForeignKeyWidget(End3, "id"),
    )

    class Meta:
        model = TechCapability
        import_id_fields = ("id",)
        fields = ("id", "end3", "status", "number")
        export_order = fields
