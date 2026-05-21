from ..api.serializers.common import SubscriberConnectionSerializer
from ..models import SubscriberConnection

all_subscriber_connections_cache_key = "gpon:all_subscriber_connections"


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
