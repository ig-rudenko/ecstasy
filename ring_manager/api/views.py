from datetime import datetime

from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response

from .decorators import ring_valid
from .permissions import RingPermission
from .serializers import RingSerializer, PointRingSerializer

from ..ring_manager import TransportRingManager, TransportRingNormalizer
from ..models import RingDev, TransportRing
from ..solutions import SolutionsPerformer, SolutionsPerformerError


class ListTransportRingsAPIView(generics.ListAPIView):
    """
    Это класс, который возвращает набор запросов объектов TransportRing, отфильтрованных текущим пользователем и
    упорядоченных по имени.
    """

    pagination_class = None
    serializer_class = RingSerializer

    def get_queryset(self):
        """
        Эта функция возвращает набор запросов объектов TransportRing, отфильтрованных текущим пользователем
        и упорядоченных по имени.
        """
        return TransportRing.objects.filter(users=self.request.user).order_by("name")


class TransportRingDetailAPIView(generics.GenericAPIView):
    permission_classes = [RingPermission]

    @ring_valid
    def get(self, request, ring_name: str, *args, **kwargs):
        """
        Эта функция извлекает объект транспортного кольца, нормализует его, собирает все интерфейсы из его истории,
        находит связь между устройствами и возвращает сериализованный ответ данных устройств кольца.
        """

        ring = get_object_or_404(TransportRing, name=ring_name)
        self.check_object_permissions(request, ring)

        # Метод `normalize()` отвечает за нормализацию данных в объекте «кольцо»,
        # что включает в себя преобразование данных в стандартизированный формат и обеспечение их согласованности
        # во всех экземплярах модели «TransportRing». Этот процесс нормализации необходим для того, чтобы данные могли
        # правильно обрабатываться и анализироваться другими частями приложения.
        TransportRingNormalizer(ring=ring).normalize()

        # trm экземпляр используется для управления транспортным кольцом, включая сбор всех интерфейсов
        # из его истории и поиск связи между устройствами.
        trm = TransportRingManager(ring=ring)
        trm.collect_all_interfaces()  # Берем из истории
        trm.find_link_between_devices()

        return Response(PointRingSerializer(trm.ring_devs, many=True).data)


class CreateSubmitSolutionsAPIView(generics.GenericAPIView):
    permission_classes = [RingPermission]

    @ring_valid
    def get(self, request, ring_name: str):
        """
        Эта функция извлекает информацию о транспортном кольце, проверяет доступность устройств, собирает интерфейсы,
        находит связи между устройствами и возвращает points и решения `solutions`, которые можно будет применить,
        чтобы перевести кольцо в оптимальное состояние.
        """

        ring = get_object_or_404(TransportRing, name=ring_name)
        self.check_object_permissions(request, ring)

        # trm экземпляр используется для управления транспортным кольцом, включая сбор всех интерфейсов,
        # поиск связи между устройствами, создания решений.
        trm = TransportRingManager(ring=ring)

        trm.check_devices_availability()  # Проверяем доступность

        trm.collect_all_interfaces()  # Собираем интерфейсы
        trm.find_link_between_devices()  # Находим связи

        points = PointRingSerializer(trm.ring_devs, many=True).data

        ring.solutions = trm.create_solutions().solutions
        ring.solution_time = datetime.now()
        ring.save(update_fields=["solutions", "solution_time"])

        return Response(
            {
                "points": points,
                "solutions": ring.solutions,
            }
        )

    @ring_valid
    def post(self, request, ring_name: str):
        """
        Эта функция выполняет набор действий над объектом транспортного кольца и возвращает ответ с количеством
        выполненных действий.
        """

        ring = get_object_or_404(TransportRing, name=ring_name)
        self.check_object_permissions(request, ring)

        if ring.status == ring.IN_PROCESS:
            return Response({"error": "Кольцо уже разворачивается в данный момент"}, status=400)

        try:
            ring.set_status_in_progress()
            performer = SolutionsPerformer(ring=ring)
            count = performer.perform_all()
        except SolutionsPerformerError as error:
            return Response({"error": error.message}, status=500)
        finally:
            ring.set_status_normal()

        return Response({"status": count})
