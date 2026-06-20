from django.contrib.auth.models import User
from rest_framework import serializers


class UserPermissionsSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    console = serializers.SerializerMethodField(allow_null=True)

    class Meta:
        model = User
        fields = ("permissions", "console")

    @staticmethod
    def get_permissions(obj: User):
        return sorted(obj.get_all_permissions())

    def get_console(self, obj: User):
        if obj.profile.console_access and obj.profile.console_url:
            return obj.profile.console_url
        return None


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_superuser",
            "is_active",
            "date_joined",
        )
