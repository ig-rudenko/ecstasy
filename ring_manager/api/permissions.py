from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from ring_manager.models import TransportRing


class RingPermission(BasePermission):
    def has_object_permission(
        self, request: Request, view: APIView, obj: TransportRing
    ) -> bool:
        """
        Эта функция проверяет, есть ли у пользователя, делающего запрос, разрешение на доступ к определенному объекту на
        основе того, находится ли его идентификатор пользователя в списке пользователей, связанных с этим объектом.

        :param request: Объект HTTP-запроса, который содержит информацию о входящем запросе, такую как пользователь,
         делающий запрос, используемый метод HTTP и любые данные, отправленные в запросе

        :param view: Параметр представления — это класс представления, к которому обращается пользователь. Он содержит
         информацию о HTTP-запросе и пользователе, делающем запрос

        :param obj: TransportRing — это экземпляр модели, представляющий объект транспортного кольца. Он передается в
         качестве аргумента в метод has_object_permission

        :return: логическое значение, указывающее, имеет ли пользователь, делающий запрос, разрешение на доступ к
         указанному объекту TransportRing.
        """
        return (
            request.user.is_superuser
            or request.user.id in obj.users.all().values_list("id", flat=True)
            and obj.status != obj.DEACTIVATED
        )


class TransportRingPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView):
        return request.user.has_perm("auth.access_transport_rings")


class AccessRingPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView):
        return request.user.has_perm("auth.access_rings")
