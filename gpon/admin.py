from django.contrib import admin

from .models import (
    Service,
    End3,
    HouseB,
    HouseOLTState,
    OLTState,
    Address,
    TechCapability,
    Customer,
    SubscriberConnection,
)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(End3)
class End3Admin(admin.ModelAdmin):
    list_display = ("type", "capacity", "address", "location")
    list_filter = ["type", "capacity"]
    list_select_related = ["address"]
    raw_id_fields = ("address",)


@admin.register(HouseB)
class HouseBAdmin(admin.ModelAdmin):
    list_display = ("address", "floors", "total_entrances", "is_building")
    list_filter = ("apartment_building", "floors", "total_entrances")
    list_select_related = ["address"]
    raw_id_fields = ("address",)

    @admin.display(description="Многоквартирное здание", boolean=True)
    def is_building(self, instance: HouseB) -> bool:
        return instance.apartment_building


@admin.register(HouseOLTState)
class HouseOLTStateAdmin(admin.ModelAdmin):
    list_display = ("house", "statement", "entrances", "end3_set_count")
    list_select_related = ["house", "statement"]
    raw_id_fields = ("house", "statement", "end3_set")

    @admin.display(description="кол-во splitter/rizers")
    def end3_set_count(self, obj: HouseOLTState):
        return obj.end3_set.count()


@admin.register(OLTState)
class OLTStateAdmin(admin.ModelAdmin):
    list_display = ("device", "olt_port")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("verbose",)


@admin.register(TechCapability)
class TechCapabilityAdmin(admin.ModelAdmin):
    list_display = ("end3", "status", "number")
    list_filter = ["status", "number"]
    list_select_related = ["end3"]
    raw_id_fields = ("end3",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "contract")
    list_filter = ["type"]
    search_fields = ["company_name", "first_name", "surname", "last_name", "phone"]


@admin.register(SubscriberConnection)
class SubscriberConnectionAdmin(admin.ModelAdmin):
    list_display = ("transit", "order", "address", "customer")
    search_fields = ["transit", "order"]
    list_select_related = ["address", "customer"]
    raw_id_fields = ("customer", "address", "tech_capability")
