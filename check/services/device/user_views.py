from dataclasses import dataclass, field
from datetime import datetime, timedelta

from django.core.cache import cache

from check.models import Devices


@dataclass
class DeviceView:
    username: str
    started: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)


class DeviceUserViews:
    cache_prefix = "device-user-view"
    view_ttl = 10  # секунд

    def __init__(self, device: Devices):
        self.device = device
        self.cache_key = f"{self.cache_prefix}:{device.id}"

    def get_viewings(self, update_expired: bool = True) -> list[DeviceView]:
        views: None | list[DeviceView] = cache.get(self.cache_key)
        if views is None:
            return []

        # Оставляем только те просмотры, которые обновлялись не позже `view_ttl` сек назад.
        filtered_views = list(
            filter(lambda dv: dv.updated > (datetime.now() - timedelta(seconds=self.view_ttl)), views)
        )

        if update_expired and len(filtered_views) != len(views):
            cache.set(self.cache_key, filtered_views, timeout=self.view_ttl + 5)

        return filtered_views

    def set_viewing(self, username: str) -> None:
        current_viewing = self.get_viewings(update_expired=False)

        for view in current_viewing:
            if view.username == username:
                view.updated = datetime.now()
                break
        else:
            current_viewing.append(DeviceView(username=username))

        cache.set(self.cache_key, current_viewing, timeout=self.view_ttl + 5)
