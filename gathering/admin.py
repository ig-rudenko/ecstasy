from django.contrib import admin
from .models import MacAddress


@admin.register(MacAddress)
class MacAddressesAdmin(admin.ModelAdmin):
    list_display = ["address", "vlan", "device", "port", "datetime"]
    list_select_related = ["device"]


