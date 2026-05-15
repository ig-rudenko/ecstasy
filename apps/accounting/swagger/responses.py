from typing import ClassVar

from rest_framework import serializers


class OIDCSwaggerSchema(serializers.Serializer):
    enabled = serializers.BooleanField()
    url = serializers.URLField()
    clientId = serializers.CharField()
    realm = serializers.CharField()
    authorizationEndpoint = serializers.URLField()
    tokenEndpoint = serializers.URLField()
    userinfoEndpoint = serializers.URLField()
    logoutEndpoint = serializers.URLField()


class UserPermissionsSwaggerSerializer(serializers.Serializer):
    permissions: ClassVar[serializers.ListSerializer] = serializers.ListSerializer(
        child=serializers.CharField(), label="Все права доступа пользователя"
    )
    console = serializers.URLField(
        allow_null=True, label="URL консоли для подключения к сетевому оборудованию"
    )
    ecstasy_loop_url = serializers.URLField(allow_null=True, label="Ссылка на внешний сервис Ecstasy Loop")
