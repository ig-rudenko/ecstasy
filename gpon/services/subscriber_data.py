from django.core.cache import cache

from gpon.api.serializers.common import SubscriberConnectionSerializer
from gpon.api.serializers.create_subscriber_data import SubscriberDataSerializer
from gpon.models import SubscriberConnection, OLTState

all_subscriber_connections_cache_key = "gpon:all_subscriber_connections"


def get_all_subscriber_connections(from_cache: bool = True):
    cache_timeout = 60 * 10

    data = None
    if from_cache:
        data = cache.get(all_subscriber_connections_cache_key)
    if data is None:
        queryset = SubscriberConnection.objects.all().select_related("customer", "address")
        data = SubscriberDataSerializer(queryset, many=True).data
        cache.set(all_subscriber_connections_cache_key, data, cache_timeout)
    return data


def get_subscribers_on_device_port(device_name: str, olt_port: str, ont_id: str):
    olt = OLTState.objects.get(device__name=device_name, olt_port=olt_port)

    subscriber_connections = [
        subscriber_connection
        for house_olt_state in olt.house_olt_states.all()
        for end3 in house_olt_state.end3_set.all()
        for tech_capability in end3.techcapability_set.all()
        for subscriber_connection in tech_capability.subscriber_connection.all().select_related("customer")
        if not ont_id or str(subscriber_connection.ont_id) == ont_id
    ]

    serializer = SubscriberConnectionSerializer(subscriber_connections, many=True)
    return serializer.data
