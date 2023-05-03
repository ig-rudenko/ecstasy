from django.contrib import admin
from .models import RingDev, TransportRing


@admin.register(TransportRing)
class TransportRingAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(RingDev)
class RingDevsAdmin(admin.ModelAdmin):
    list_display = ["device"]
