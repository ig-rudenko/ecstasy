import orjson
from django.db.models import QuerySet
from django.db.transaction import atomic
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.response import Response

from check.models import Devices
from devicemanager.device import Interfaces

from ..models import End3, HouseB, HouseOLTState, OLTState, TechCapability
from ..services.tech_data import get_all_tech_data
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
    ViewHouseBTechDataSerializer,
    ViewOLTStatesTechDataSerializer,
)


class ListUserPermissions(GenericAPIView):
    def get(self, *args, **kwargs):
        permissions = filter(lambda x: x.startswith("gpon"), self.request.user.get_all_permissions())
        return Response(permissions)


class TechDataListCreateAPIView(GenericAPIView):
    """
    Предназначен для создания и просмотра технических данных
    """

    permission_classes = [TechDataPermission]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateTechDataSerializer

    def get(self, request) -> Response:
        data = get_all_tech_data()
        return Response(data)

    def post(self, request):
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

    def get(self, request, *args, **kwargs):
        olt_state = self.get_object()
        serializer = self.get_serializer(instance=olt_state)
        return Response(serializer.data)


class ViewBuildingTechDataAPIView(RetrieveAPIView):
    serializer_class = ViewHouseBTechDataSerializer
    permission_classes = [TechDataPermission]

    def get_queryset(self):
        if self.request.method == "GET":
            queryset = (
                HouseB.objects.all()
                .select_related("address")
                .prefetch_related(
                    "house_olt_states",
                    "house_olt_states__statement",
                    "house_olt_states__end3_set__address",
                    "house_olt_states__statement__device",
                )
            )
            return queryset
        return HouseB.objects.all()


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
        if not port and not device:
            return queryset

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

        return queryset.filter(address_id__in=addresses_ids)


class End3AddressesListAPIView(ListAPIView):
    """Возвращает список сплиттеров/райзеров вместе с их адресами"""

    serializer_class = End3Serializer
    queryset = End3.objects.select_related("address")


class DevicesNamesListAPIView(GenericAPIView):
    def get_queryset(self):
        """
        ## Возвращаем queryset всех устройств из доступных для пользователя групп
        """
        return Devices.objects.filter(group__profile__user=self.request.user)

    def get(self, request, *args, **kwargs) -> Response:
        device_names = self.get_queryset().values_list("name", flat=True)
        return Response(device_names)


class DevicePortsList(DevicesNamesListAPIView):
    def get(self, request, *args, **kwargs) -> Response:
        try:
            device: Devices = self.get_queryset().only("id").get(name=self.kwargs["device_name"])
        except Devices.DoesNotExist:
            return Response({"error": "Оборудование не существует"}, status=400)

        interfaces = Interfaces(orjson.loads(device.devicesinfo.interfaces or "[]"))

        interfaces_names = list(map(lambda x: x.name, interfaces))
        return Response(interfaces_names)


class End3TechCapabilityAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = End3TechCapabilitySerializer
    permission_classes = [End3Permission]

    def get_queryset(self):
        if self.request.method == "GET":
            queryset = (
                End3.objects.all()
                .select_related("address")
                .prefetch_related("techcapability_set", "techcapability_set__subscriber_connection")
            )
            return queryset
        return End3.objects.all()


class End3CreateAPIView(GenericAPIView):
    queryset = End3.objects.all()
    serializer_class = AddEnd3ToHouseOLTStateSerializer
    permission_classes = [End3Permission]

    def post(self, request, *args, **kwargs) -> Response:
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        end3_list: list[End3] = serializer.save()
        return Response(End3Serializer(end3_list, many=True).data, status=201)


class TechCapabilityAPIView(RetrieveUpdateAPIView):
    serializer_class = TechCapabilitySerializer
    permission_classes = [TechCapabilityPermission]

    def get_queryset(self):
        if self.request.method == "GET":
            queryset = TechCapability.objects.all().prefetch_related("subscriber_connection")
            return queryset
        return TechCapability.objects.all()


class RetrieveUpdateOLTStateAPIView(RetrieveUpdateAPIView):
    serializer_class = UpdateRetrieveOLTStateSerializer
    permission_classes = [OLTStatePermission]

    def get_queryset(self):
        if self.request.method == "GET":
            queryset = (
                OLTState.objects.all()
                .select_related("device")
                .only("device__name", "olt_port", "fiber", "description")
            )
            return queryset
        return OLTState.objects.all()


class RetrieveUpdateHouseOLTState(RetrieveUpdateAPIView):
    permission_classes = [HouseOLTStatePermission]

    def get_queryset(self):
        if self.request.method == "GET":
            queryset = (
                HouseOLTState.objects.all()
                .select_related("house")
                .prefetch_related("end3_set", "end3_set__address")
            )
            return queryset
        return HouseOLTState.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return StructuresHouseOLTStateSerializer
        return UpdateHouseOLTStateSerializer
