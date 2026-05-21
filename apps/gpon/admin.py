from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RangeDateTimeFilter, RelatedDropdownFilter
from unfold.contrib.import_export.forms import ImportForm, SelectableFieldsExportForm

from ecstasy_project.admin_filters import distinct_dropdown_filter

from .export_resources import (
    AddressResource,
    CustomerResource,
    End3Resource,
    ServiceResource,
    TechCapabilityResource,
)
from .models import (
    Address,
    Customer,
    End3,
    HouseB,
    HouseOLTState,
    OLTState,
    Service,
    SubscriberConnection,
    TechCapability,
)

CapacityDropdownFilter = distinct_dropdown_filter("capacity", "capacity")
FloorsDropdownFilter = distinct_dropdown_filter("floors", "floors")
EntrancesDropdownFilter = distinct_dropdown_filter("total_entrances", "total entrances")
NumberDropdownFilter = distinct_dropdown_filter("number", "number")


class TechCapabilityRelatedDropdownFilter(RelatedDropdownFilter):
    """Related dropdown with preloaded `end3 -> address` for labels."""

    def field_choices(self, field, request: HttpRequest, model_admin: ModelAdmin):
        """Build choices without N+1 from `TechCapability.__str__`."""
        del field
        capability_ids = (
            model_admin.get_queryset(request)
            .order_by()
            .values_list("tech_capability_id", flat=True)
            .distinct()
        )
        capabilities = (
            TechCapability.objects.filter(pk__in=capability_ids)
            .select_related("end3__address")
            .only(
                "id",
                "end3__location",
                "end3__address__region",
                "end3__address__settlement",
                "end3__address__plan_structure",
                "end3__address__street",
                "end3__address__house",
                "end3__address__block",
                "end3__address__floor",
                "end3__address__apartment",
            )
        )
        return [(capability.pk, str(capability)) for capability in capabilities]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet | None:
        """Apply selected filter value and keep related data joined."""
        qs = super().queryset(request, queryset)
        if qs is not None:
            return qs.select_related("tech_capability__end3__address")
        return qs


@admin.register(Service)
class ServiceAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    resource_class = ServiceResource
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(End3)
class End3Admin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    resource_class = End3Resource
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = ("type", "capacity", "address", "location")
    list_filter = (("type", ChoicesDropdownFilter), CapacityDropdownFilter)
    list_select_related = ["address"]
    autocomplete_fields = ("address",)
    search_fields = ("location", "address__street", "address__house")
    fieldsets = (
        ("Основное", {"classes": ("tab",), "fields": ("type", "capacity", "location")}),
        ("Адрес", {"classes": ("tab",), "fields": ("address",)}),
    )


@admin.register(HouseB)
class HouseBAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = ("address", "floors", "total_entrances", "is_building")
    list_filter = ("apartment_building", FloorsDropdownFilter, EntrancesDropdownFilter)
    list_select_related = ["address"]
    autocomplete_fields = ("address",)
    search_fields = ("address__street", "address__house", "address__settlement")
    fieldsets = (
        ("Здание", {"classes": ("tab",), "fields": ("address", "apartment_building")}),
        ("Параметры", {"classes": ("tab",), "fields": ("floors", "total_entrances")}),
    )

    @admin.display(description="Многоквартирное здание", boolean=True)
    def is_building(self, instance: HouseB) -> bool:
        """Return the building type in a boolean column."""
        return instance.apartment_building


@admin.register(HouseOLTState)
class HouseOLTStateAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = ("house", "statement", "entrances", "end3_set_count")
    list_select_related = ["house", "statement", "statement__device"]
    autocomplete_fields = ("house", "statement", "end3_set")
    list_filter = (("statement", RelatedDropdownFilter),)
    search_fields = ("house__address__street", "house__address__house", "statement__olt_port")
    fieldsets = (
        ("Связи", {"classes": ("tab",), "fields": ("house", "statement", "end3_set")}),
        ("Описание", {"classes": ("tab",), "fields": ("entrances", "description")}),
    )

    @admin.display(description="Кол-во splitter/rizers")
    def end3_set_count(self, obj: HouseOLTState) -> int:
        """Return the number of linked end3 objects."""
        return obj.end3_set.count()


@admin.register(OLTState)
class OLTStateAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = ("device", "olt_port", "fiber")
    list_select_related = ["device"]
    autocomplete_fields = ("device",)
    search_fields = ("device__name", "olt_port", "fiber", "description")
    list_filter = (("device", RelatedDropdownFilter),)
    fieldsets = (
        ("Основное", {"classes": ("tab",), "fields": ("device", "olt_port", "fiber")}),
        ("Описание", {"classes": ("tab",), "fields": ("description",)}),
    )


@admin.register(Address)
class AddressAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    resource_class = AddressResource
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ("verbose", "settlement", "street", "house")
    search_fields = ("region", "settlement", "plan_structure", "street", "house")
    fieldsets = (
        ("Локация", {"classes": ("tab",), "fields": ("region", "settlement", "plan_structure")}),
        ("Адрес", {"classes": ("tab",), "fields": ("street", "house", "block")}),
        ("Детализация", {"classes": ("tab",), "fields": ("floor", "apartment")}),
    )


@admin.register(TechCapability)
class TechCapabilityAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    resource_class = TechCapabilityResource
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = ("end3", "status", "number")
    list_filter = (("status", ChoicesDropdownFilter), NumberDropdownFilter)
    list_select_related = ["end3", "end3__address"]
    autocomplete_fields = ("end3",)
    search_fields = ("end3__location", "end3__address__street", "end3__address__house")


@admin.register(Customer)
class CustomerAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    resource_class = CustomerResource
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = ("full_name", "phone", "contract")
    list_filter = (("type", ChoicesDropdownFilter),)
    search_fields = ("company_name", "first_name", "surname", "last_name", "phone", "contract")
    fieldsets = (
        ("Тип", {"classes": ("tab",), "fields": ("type", "contract")}),
        ("Физлицо", {"classes": ("tab",), "fields": ("surname", "first_name", "last_name")}),
        ("Компания", {"classes": ("tab",), "fields": ("company_name",)}),
        ("Контакт", {"classes": ("tab",), "fields": ("phone",)}),
    )


@admin.register(SubscriberConnection)
class SubscriberConnectionAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = ("transit", "order", "address", "customer", "connected_at")
    search_fields = ("transit", "order", "ont_serial", "ont_mac", "ip")
    list_select_related = True
    autocomplete_fields = ("customer", "address", "tech_capability", "services")
    list_filter = (
        ("customer", RelatedDropdownFilter),
        ("address", RelatedDropdownFilter),
        ("tech_capability", TechCapabilityRelatedDropdownFilter),
        ("connected_at", RangeDateTimeFilter),
    )
    fieldsets = (
        ("Абонент", {"classes": ("tab",), "fields": ("customer", "address", "tech_capability")}),
        (
            "Подключение",
            {
                "classes": ("tab",),
                "fields": ("order", "transit", "connected_at", "description"),
            },
        ),
        ("ONT", {"classes": ("tab",), "fields": ("ont_id", "ont_serial", "ont_mac", "ip")}),
        ("Услуги", {"classes": ("tab",), "fields": ("services",)}),
    )
