from django.core.cache import cache

from gpon.api.serializers.common import SubscriberConnectionSerializer
from gpon.api.serializers.create_subscriber_data import SubscriberDataSerializer
from gpon.models import SubscriberConnection

all_subscriber_connections_cache_key = "gpon:all_subscriber_connections"


def get_all_subscriber_connections(from_cache: bool = True):
    cache_timeout = 1

    data = None
    if from_cache:
        data = cache.get(all_subscriber_connections_cache_key)
    if data is None:
        queryset = (
            SubscriberConnection.objects.all()
            .select_related("address", "customer")
            .prefetch_related("services")
        )
        data = SubscriberDataSerializer(queryset, many=True).data
        cache.set(all_subscriber_connections_cache_key, data, cache_timeout)
    return data


def get_subscribers_on_device_port(device_name: str, olt_port: str, ont_id: int):
    subscriber_connections = (
        SubscriberConnection.objects.filter(
            tech_capability__end3__house_olt_states__statement__device__name=device_name,
            tech_capability__end3__house_olt_states__statement__olt_port=olt_port,
        )
        .select_related("customer", "address")
        .prefetch_related("services")
    )

    if ont_id:
        subscriber_connections = subscriber_connections.filter(ont_id=ont_id)

    serializer = SubscriberConnectionSerializer(subscriber_connections, many=True)
    return serializer.data
