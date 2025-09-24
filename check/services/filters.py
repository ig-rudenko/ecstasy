from django.contrib.auth.models import AbstractUser, AnonymousUser, User
from django.db.models import Q, QuerySet

from check.models import Devices


def filter_devices_qs_by_user(
    qs: QuerySet[Devices], user: User | AnonymousUser | AbstractUser
) -> QuerySet[Devices]:
    """
    Функция фильтрации устройств по пользователю.

    Если пользователь является суперпользователем, то дополнительные фильтры не применяются.
    Если пользователь является анонимным, то возвращается пустой QuerySet.

    В других случаях проверяется что группа оборудования доступна в профиле пользователя или
    у пользователя есть группы доступа с данным оборудованием и нет групп запрета с данным оборудованием.
    """
    if user.is_superuser:
        return qs
    elif user.is_anonymous:
        return qs.none()

    return (
        qs.filter(
            Q(group__profile__user_id=user.id)  # доступ через профиль
            | Q(access_groups__users=user)
            | Q(access_groups__user_groups__in=user.groups.all())
        )
        .exclude(
            Q(forbidden_access_groups__users=user)
            | Q(forbidden_access_groups__user_groups__in=user.groups.all())
        )
        .distinct()
    )
