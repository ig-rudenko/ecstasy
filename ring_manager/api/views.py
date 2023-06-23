from datetime import datetime

from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response

from .decorators import ring_valid
from .permissions import RingPermission
from .serializers import TransportRingSerializer, PointRingSerializer

from ..ring_manager import TransportRingManager
from ..models import TransportRing
from ..solutions import SolutionsPerformer, Solutions, SolutionsPerformerError


class ListTransportRingsAPIView(generics.ListAPIView):
    """
    Это класс, который возвращает набор запросов объектов TransportRing, отфильтрованных текущим пользователем и
    упорядоченных по имени.
    """

    pagination_class = None
    serializer_class = TransportRingSerializer

    def get_queryset(self):
        """
        Эта функция возвращает набор запросов объектов TransportRing, отфильтрованных текущим пользователем
        и упорядоченных по имени.
        """
        return TransportRing.objects.filter(users=self.request.user).order_by("name")


class TransportRingStatusAPIView(generics.GenericAPIView):
    permission_classes = [RingPermission]

    @ring_valid
    def get(self, request, ring_name: str, *args, **kwargs):
        """
        Эта функция извлекает состояние транспортного кольца и возвращает информацию о том,
        активно ли оно и разворачивается ли в данный момент.
        """

        ring = get_object_or_404(TransportRing, name=ring_name)
        self.check_object_permissions(request, ring)
        return Response(
            {"active": ring.status != ring.DEACTIVATED, "rotating": ring.status == ring.IN_PROCESS}
        )


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

        # trm экземпляр используется для управления транспортным кольцом, включая сбор всех интерфейсов
        # из его истории и поиск связи между устройствами.
        trm = TransportRingManager(ring=ring)

        # Метод `normalize()` отвечает за нормализацию данных в объекте «кольцо»,
        # что включает в себя преобразование данных в стандартизированный формат и обеспечение их согласованности
        # во всех экземплярах модели «TransportRing». Этот процесс нормализации необходим для того, чтобы данные могли
        # правильно обрабатываться и анализироваться другими частями приложения.
        trm.normalize()

        trm.collect_all_interfaces()  # Берем из истории
        trm.find_link_between_devices()
        points = PointRingSerializer(trm.ring_devs, many=True).data
        return Response(
            {
                "points": points,
                "active": ring.status != ring.DEACTIVATED,
                "rotating": ring.status == ring.IN_PROCESS,
            }
        )


class GetLastSolutionsAPIView(generics.GenericAPIView):
    permission_classes = [RingPermission]

    @ring_valid
    def get(self, request, ring_name: str):
        ring = get_object_or_404(TransportRing, name=ring_name)
        self.check_object_permissions(request, ring)

        last_solutions_time = 0
        solutions = Solutions()

        # Есть ли какие-либо решения и не истек ли срок действия последнего решения.
        if ring.solutions and not SolutionsPerformer.is_solution_expired(ring.solution_time):
            solutions = Solutions.from_ring_history(ring)
            last_solutions_time = ring.solution_time.timestamp()

        return Response(
            {
                "solutions": solutions.solutions,
                "solutionsTime": last_solutions_time,
                # Все ли решения безопасны или нет.
                "safeSolutions": solutions.has_only_safe_solutions,
            }
        )


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

        # Создаем решения
        solution_manager = trm.create_solutions()

        # Записываем в БД
        ring.solutions = solution_manager.solutions
        ring.solution_time = datetime.now()
        ring.save(update_fields=["solutions", "solution_time"])

        return Response(
            {
                "points": PointRingSerializer(trm.ring_devs, many=True).data,
                "solutions": ring.solutions,
                "safeSolutions": solution_manager.has_only_safe_solutions,
            }
        )

    @ring_valid
    def post(self, request, ring_name: str):
        """
        Эта функция выполняет набор действий над объектом транспортного кольца и возвращает выполненные действия,
        а также их статус
        """

        ring = get_object_or_404(TransportRing, name=ring_name)
        self.check_object_permissions(request, ring)

        if ring.status == ring.IN_PROCESS:
            return Response({"error": "Кольцо уже разворачивается в данный момент"}, status=400)

        ring.set_status_in_progress()  # Отмечаем, что кольцо будет далее использоваться
        try:
            # Инициализируем исполнителя решений для кольца
            performer = SolutionsPerformer(ring=ring)
            performed_solutions = performer.perform_all()  # Выполняем решения

        except SolutionsPerformerError:
            # Обязательно надо вернуть статус кольца в нормальное состояние
            ring.set_status_normal(clear_solutions=True)
            raise  # Продолжаем ошибку

        # Смотрим статус кольца
        trm = TransportRingManager(ring=ring)
        trm.check_devices_availability()  # Проверяем доступность
        trm.collect_all_interfaces()  # Собираем интерфейсы
        trm.find_link_between_devices()
        points = PointRingSerializer(trm.ring_devs, many=True).data

        return Response(
            {
                "solutions": performed_solutions,
                "points": points,
            }
        )
