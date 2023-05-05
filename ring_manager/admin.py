from django.contrib import admin
from .models import RingDev, TransportRing


@admin.register(TransportRing)
class TransportRingAdmin(admin.ModelAdmin):
    list_display = ["name"]
    readonly_fields = ["status", "solutions", "solution_time"]


@admin.register(RingDev)
class RingDevsAdmin(admin.ModelAdmin):
    list_display = ["device"]
