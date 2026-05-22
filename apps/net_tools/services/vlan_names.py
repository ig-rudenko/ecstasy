from django.core.cache import BaseCache, cache

from ..models import VlanName


class VlanNamesCache:
    cache_key: str = "vlan_names"
    default_cache_obj: BaseCache = cache

    def __init__(self, cache_obj: BaseCache | None = None, cache_timeout: int = 60 * 60 * 24):
        self.cache = cache_obj or self.default_cache_obj
        self.cache_timeout = cache_timeout or 60 * 60 * 24

    def get_all_vlan_names(self) -> dict[str, str]:
        cached_data = self.cache.get(self.cache_key)
        if cached_data is not None:
            return cached_data

        vlan_names = {str(v["vid"]): v["name"] or "" for v in VlanName.objects.all().values("vid", "name")}
        self.cache.set(self.cache_key, vlan_names, timeout=self.cache_timeout)
        return vlan_names

    @classmethod
    def clear_cache(cls, cache_obj: BaseCache | None = None):
        if cache_obj is None:
            cls.default_cache_obj.delete(cls.cache_key)
        else:
            cache_obj.delete(cls.cache_key)
