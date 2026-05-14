from django.core.cache import cache
from django.db.models import QuerySet

from ..api.serializers.address import AddressSerializer
from ..api.serializers.create_tech_data import OLTStateSerializer
from ..models import End3, HouseB, HouseOLTState


def _contains(haystack: str, needle: str) -> bool:
    if not needle:
        return True
    return needle.lower() in (haystack or "").lower()


def _matches_filters(item: dict, filters: dict) -> bool:
    address = item.get("address", {})
    return (
        _contains(address.get("region", ""), filters.get("region", ""))
        and _contains(address.get("settlement", ""), filters.get("settlement", ""))
        and _contains(address.get("planStructure", ""), filters.get("planStructure", ""))
        and _contains(address.get("street", ""), filters.get("street", ""))
        and _contains(address.get("house", ""), filters.get("house", ""))
        and _contains(str(address.get("block", "") or ""), str(filters.get("block", "") or ""))
        and _contains(item.get("deviceName", ""), filters.get("deviceName", ""))
        and _contains(item.get("devicePort", ""), filters.get("devicePort", ""))
    )


def get_all_tech_data(from_cache: bool = True, filters: dict | None = None):
    cache_key = "gpon:api:TechDataListCreateAPIView:get"
    cache_timeout = 60 * 10  # секунд.

    filters = filters or {}
    has_filters = any(str(value or "").strip() for value in filters.values())

    data = []
    if from_cache and not has_filters:
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

    if has_filters:
        return [item for item in data if _matches_filters(item, filters)]

    cache.set(cache_key, data, timeout=cache_timeout)
    return data
