from django.core.cache import cache
from django.db.models import QuerySet

from gpon.api.serializers.address import AddressSerializer
from gpon.api.serializers.create_tech_data import OLTStateSerializer
from gpon.models import End3, HouseB, HouseOLTState


def get_all_tech_data(from_cache: bool = True):
    cache_key = "gpon:api:TechDataListCreateAPIView:get"
    cache_timeout = 60 * 10  # секунд.

    data = []
    if from_cache:
        data = cache.get(cache_key, [])
    if data:
        return data

    buildings: QuerySet[HouseB] = HouseB.objects.all().select_related("address")
    for house in buildings:
        house_olt_states_queryset: QuerySet[HouseOLTState] = (
            house.house_olt_states.all()
            .select_related("statement", "statement__device")
            .prefetch_related("end3_set")
        )
        for house_olt_state in house_olt_states_queryset:
            end3: End3 | None = house_olt_state.end3_set.first()

            data.append(
                {
                    **OLTStateSerializer(instance=house_olt_state.statement).data,
                    "address": AddressSerializer(instance=house.address).data,
                    "building_type": house.type,
                    "building_id": house.id,
                    "entrances": house_olt_state.entrances,
                    "customerLine": {
                        "type": end3.type if end3 else None,
                        "count": house_olt_state.end3_set.count(),
                        "typeCount": end3.capacity if end3 else None,
                    },
                }
            )

    cache.set(cache_key, data, timeout=cache_timeout)
    return data
