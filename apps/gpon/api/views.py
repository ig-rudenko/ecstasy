import orjson
from django.db.models import Q, QuerySet
from django.db.transaction import atomic
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.response import Response

from apps.check.api.views.paginators import End3PageNumberPagination
from apps.check.models import Devices
from devicemanager.device import Interfaces
from ecstasy_project.types.api import PageSizePageNumberPagination

from ..models import End3, HouseB, HouseOLTState, OLTState, TechCapability
from .filters import End3Filer, TechDataFilter
from .permissions import (
    End3Permission,
    HouseOLTStatePermission,
    OLTStatePermission,
    TechCapabilityPermission,
    TechDataPermission,
)
from .serializers.address import BuildingAddressSerializer
from .serializers.common import End3Serializer
from .serializers.create_tech_data import (
    AddEnd3ToHouseOLTStateSerializer,
    CreateTechDataSerializer,
)
from .serializers.update_tech_data import (
    End3TechCapabilitySerializer,
    UpdateHouseOLTStateSerializer,
    UpdateRetrieveOLTStateSerializer,
)
from .serializers.view_tech_data import (
    StructuresHouseOLTStateSerializer,
    TechCapabilitySerializer,
    TechDataListSerializer,
    ViewHouseBTechDataSerializer,
    ViewOLTStatesTechDataSerializer,
)
from .swagger import (
    buildings_addresses_list_api_doc,
    device_ports_list_api_doc,
    devices_names_list_api_doc,
    list_user_permissions_api_doc,
    tech_data_create_api_doc,
    tech_data_list_api_doc,
    view_olt_state_tech_data_api_doc,
)


class ListUserPermissions(GenericAPIView):
    pagination_class = None

    @list_user_permissions_api_doc
    def get(self, *args, **kwargs):
        permissions = filter(lambda x: x.startswith("gpon"), self.request.user.get_all_permissions())
        return Response(permissions)


class TechDataListCreateAPIView(ListCreateAPIView):
    """
    Предназначен для создания и просмотра технических данных
    """

    queryset = HouseOLTState.objects.all()
    permission_classes = [TechDataPermission]
    pagination_class = PageSizePageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = TechDataFilter

    def get_queryset(self):
        if self.request.method == "GET":
            return (
                HouseOLTState.objects.all()
                .select_related("house", "house__address", "statement", "statement__device")
                .prefetch_related("end3_set")
                .order_by("id")
            )
        return HouseOLTState.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return TechDataListSerializer
        return CreateTechDataSerializer

    @tech_data_list_api_doc
    def get(self, request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)

    @tech_data_create_api_doc
    def post(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with atomic():
            serializer.create(serializer.validated_data)
        return Response(serializer.data, status=201)


class ViewOLTStateTechDataAPIView(GenericAPIView):
    serializer_class = ViewOLTStatesTechDataSerializer
    permission_classes = [TechDataPermission]

    def get_queryset(self):
        return (
            OLTState.objects.all()
            .select_related("device")
            .prefetch_related(
                "house_olt_states",
                "house_olt_states__end3_set",
                "house_olt_states__end3_set__address",
            )
        )

    def get_object(self):
        device_name = self.kwargs["device_name"]
        olt_port = self.request.GET.get("port")

        try:
            return self.get_queryset().get(device__name=device_name, olt_port=olt_port)
        except OLTState.DoesNotExist as exc:
            raise ValidationError(
                f"Не удалось найти OLT подключение оборудования {device_name} на порту {olt_port}"
            ) from exc

    @view_olt_state_tech_data_api_doc
    def get(self, request, *args, **kwargs):
        olt_state = self.get_object()
        serializer = self.get_serializer(instance=olt_state)
        return Response(serializer.data)


class ViewBuildingTechDataAPIView(RetrieveAPIView):
    serializer_class = ViewHouseBTechDataSerializer
    permission_classes = [TechDataPermission]

    def get_queryset(self):
        if self.request.method == "GET":
            return (
                HouseB.objects.all()
                .select_related("address")
                .prefetch_related(
                    "house_olt_states",
                    "house_olt_states__statement",
                    "house_olt_states__end3_set__address",
                    "house_olt_states__statement__device",
                )
            )
        return HouseB.objects.all()


@method_decorator(name="get", decorator=buildings_addresses_list_api_doc)
class BuildingsAddressesListAPIView(ListAPIView):
    serializer_class = BuildingAddressSerializer
    queryset = HouseB.objects.all().select_related("address")

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        """
        Если были переданы оборудование и порт, то отфильтровывает сплиттера,
        которые имеются только у данного порта.
        """
        port = self.request.GET.get("port")
        device = self.request.GET.get("device")
        if port or device:
            try:
                olt_state: OLTState = OLTState.objects.get(olt_port=port, device__name=device)
            except OLTState.DoesNotExist:
                return queryset.none()
            addresses_ids = set()
            house_olt_states_queryset: QuerySet[HouseOLTState] = olt_state.house_olt_states.all()
            for house_olt_state in house_olt_states_queryset:
                addresses_ids |= set(
                    house_olt_state.end3_set.all().select_related("address").values_list("address", flat=True)
                )

            queryset = queryset.filter(address_id__in=addresses_ids)

        search_query = str(self.request.GET.get("search", "")).strip()
        if search_query:
            queryset = queryset.filter(
                Q(address__region__icontains=search_query)
                | Q(address__settlement__icontains=search_query)
                | Q(address__plan_structure__icontains=search_query)
                | Q(address__street__icontains=search_query)
                | Q(address__house__icontains=search_query)
            )

        return queryset


class End3AddressesListAPIView(ListAPIView):
    """Возвращает список сплиттеров/райзеров вместе с их адресами"""

    serializer_class = End3Serializer
    queryset = End3.objects.select_related("address")

    def get_queryset(self):
        queryset = super().get_queryset()
        address_id = self.request.GET.get("address_id")
        if address_id:
            queryset = queryset.filter(address_id=address_id)
        search_query = str(self.request.GET.get("search", "")).strip()
        if search_query:
            queryset = queryset.filter(
                Q(type__icontains=search_query)
                | Q(location__icontains=search_query)
                | Q(address__region__icontains=search_query)
                | Q(address__settlement__icontains=search_query)
                | Q(address__plan_structure__icontains=search_query)
                | Q(address__street__icontains=search_query)
                | Q(address__house__icontains=search_query)
            )
        return queryset


class DevicesNamesListAPIView(GenericAPIView):
    pagination_class = None

    def get_queryset(self):
        """
        ## Возвращаем queryset всех устройств из доступных для пользователя групп
        """
        return Devices.objects.filter(group__profile__user=self.request.user)

    @devices_names_list_api_doc
    def get(self, request, *args, **kwargs) -> Response:
        device_names = self.get_queryset().values_list("name", flat=True)
        return Response(device_names)


class DevicePortsList(DevicesNamesListAPIView):
    pagination_class = None

    @device_ports_list_api_doc
    def get(self, request, *args, **kwargs) -> Response:
        try:
            device: Devices = self.get_queryset().only("id").get(name=self.kwargs["device_name"])
        except Devices.DoesNotExist as exc:
            raise NotFound("Оборудование не существует") from exc

        interfaces = Interfaces(orjson.loads(device.devicesinfo.interfaces or "[]"))

        interfaces_names = list(map(lambda x: x.name, interfaces))
        return Response(interfaces_names)


class End3TechCapabilityAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = End3TechCapabilitySerializer
    permission_classes = [End3Permission]

    def get_queryset(self):
        if self.request.method == "GET":
            return (
                End3.objects.all()
                .select_related("address")
                .prefetch_related("techcapability_set", "techcapability_set__subscriber_connection")
            )
        return End3.objects.all()


class End3CreateAPIView(ListCreateAPIView):
    permission_classes = [End3Permission]
    filter_backends = [DjangoFilterBackend]
    pagination_class = End3PageNumberPagination
    filterset_class = End3Filer

    def get_queryset(self):
        if self.request.method == "GET":
            return (
                End3.objects.all()
                .distinct()
                .select_related("address")
                .prefetch_related(
                    "techcapability_set",
                    "techcapability_set__subscriber_connection",
                    "techcapability_set__subscriber_connection__customer",
                )
                .order_by("-id")
            )

        return End3.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return End3TechCapabilitySerializer
        return AddEnd3ToHouseOLTStateSerializer

    def post(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        end3_list: list[End3] = serializer.save()
        return Response(End3Serializer(end3_list, many=True).data, status=201)


class TechCapabilityAPIView(RetrieveUpdateAPIView):
    serializer_class = TechCapabilitySerializer
    permission_classes = [TechCapabilityPermission]

    def get_queryset(self):
        if self.request.method == "GET":
            return TechCapability.objects.all().prefetch_related("subscriber_connection")
        return TechCapability.objects.all()


class RetrieveUpdateOLTStateAPIView(RetrieveUpdateAPIView):
    serializer_class = UpdateRetrieveOLTStateSerializer
    permission_classes = [OLTStatePermission]

    def get_queryset(self):
        if self.request.method == "GET":
            return (
                OLTState.objects.all()
                .select_related("device")
                .only("device__name", "olt_port", "fiber", "description")
            )
        return OLTState.objects.all()


class RetrieveUpdateHouseOLTState(RetrieveUpdateAPIView):
    permission_classes = [HouseOLTStatePermission]

    def get_queryset(self):
        if self.request.method == "GET":
            return (
                HouseOLTState.objects.all()
                .select_related("house")
                .prefetch_related("end3_set", "end3_set__address")
            )
        return HouseOLTState.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return StructuresHouseOLTStateSerializer
        return UpdateHouseOLTStateSerializer
