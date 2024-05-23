from django.contrib.auth.models import User
from rest_framework import serializers


class UserPermissionsSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("permissions",)

    @staticmethod
    def get_permissions(obj: User):
        return obj.get_all_permissions()


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
