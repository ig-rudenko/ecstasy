from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import DeviceGroup, Devices, AuthGroup, Bras, Profile, UsersActions, LogsElasticStackSettings
from django.utils.safestring import mark_safe


@admin.register(DeviceGroup)
class DeviceGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(Devices)
class DevicesAdmin(admin.ModelAdmin):
    list_display = ['ip', 'name', 'vendor', 'model', 'group', 'auth_group', 'intf_scan', 'intf_last']
    search_fields = ['ip', 'name']
    list_per_page = 50
    list_filter = ['vendor', 'model', 'group', 'auth_group']
    fieldsets = (
        ('Характеристика', {'fields': ('ip', 'name')}),
        ('Тип', {'fields': ('vendor', 'model')}),
        ('Принадлежность', {'fields': ('group', 'auth_group')}),
        ('Удаленное подключение', {'fields': ('snmp_community', 'port_scan_protocol', 'cmd_protocol')})
    )

    @admin.display(description='SCAN')
    def intf_scan(self, obj: Devices):
        return mark_safe(f'<a target="_blank" href="{obj.get_absolute_url()}?current_status=1">SCAN</a>')

    @admin.display(description='LAST')
    def intf_last(self, obj: Devices):
        return mark_safe(f'<a target="_blank" href="{obj.get_absolute_url()}">LAST</a>')


@admin.register(AuthGroup)
class AuthGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'login', 'description']
    search_fields = ['name', 'login']


@admin.register(Bras)
class BrasAdmin(admin.ModelAdmin):
    list_display = ['name', 'ip']
    search_fields = ['name', 'ip']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'permissions']

    @admin.display(description='Пользователь')
    def user(self, obj: Profile):
        return obj.user.username


admin.site.unregister(User)


@admin.register(User)
class UserProfileAdmin(UserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_superuser', 'last_login',
                    'permission', 'dev_groups']

    @admin.display(description='Права')
    def permission(self, obj: User):
        return Profile.objects.get(user_id=obj.pk).permissions

    @admin.display(description='Группы')
    def dev_groups(self, obj: User):
        s = ''
        for g in obj.profile.devices_groups.all():
            s += f'<li>{g}</li>'
        return mark_safe(s)


@admin.register(UsersActions)
class UsersActionsAdmin(admin.ModelAdmin):
    list_display = ['time', 'user', 'device', 'action']
    list_filter = ['user']
    search_fields = ['action']
    readonly_fields = list_display
    list_per_page = 50


@admin.register(LogsElasticStackSettings)
class LogsElasticStackSettingsAdmin(admin.ModelAdmin):
    list_display = ['kibana_url', 'time_range', 'query_str']