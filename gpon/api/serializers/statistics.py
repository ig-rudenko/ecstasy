from rest_framework import serializers

from gpon.models import SubscriberConnection


class OLTSubscriberSerializer(serializers.ModelSerializer):
    oltPort = serializers.CharField(source="olt_port")
    count = serializers.IntegerField()

    class Meta:
        model = SubscriberConnection
        fields = ("oltPort", "count")
