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
