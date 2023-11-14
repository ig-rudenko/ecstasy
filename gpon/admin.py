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
    list_filter = ["type"]


@admin.register(HouseB)
class HouseBAdmin(admin.ModelAdmin):
    list_display = ("address", "floors", "total_entrances")


@admin.register(HouseOLTState)
class HouseOLTStateAdmin(admin.ModelAdmin):
    list_display = ("house", "statement", "entrances", "end3_set_count")

    @admin.display(description="end3_count")
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


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "company_name", "phone", "contract")


@admin.register(SubscriberConnection)
class SubscriberConnectionAdmin(admin.ModelAdmin):
    list_display = ("transit", "order", "address", "customer")
