from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response

from .serializers import (
    CreateTechDataSerializer,
    AddressSerializer,
    ListTechDataSerializer,
    OLTStateSerializer,
)
from ..models import End3, Address, HouseB, HouseOLTState


class TechDataListCreateAPIView(GenericAPIView):
    """
    Предназначен для создания и просмотра технических данных
    """

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateTechDataSerializer
        return ListTechDataSerializer

    def get(self, request) -> Response:
        data = []

        buildings = (
            HouseB.objects.all().select_related("address")
            # .prefetch_related(
            #     "olt_states",
            #     "olt_states__houses",
            #     "end3_set",
            # )
        )
        for house in buildings:
            house: HouseB
            for house_olt_state in (
                    house.house_olt_state.all()
                            .select_related("statement", "statement__device")
                            .prefetch_related("house__end3_set")
            ):
                house_olt_state: HouseOLTState
                end3: End3 = house_olt_state.house.end3_set.first()
                data.append(
                    {
                        **OLTStateSerializer(instance=house_olt_state.statement).data,
                        "address": AddressSerializer(instance=house.address).data,
                        "entrances": house_olt_state.entrances,
                        "customerLine": {
                            "type": end3.type,
                            "count": house_olt_state.house.end3_set.count(),
                            "typeCount": end3.capacity,
                        },
                    }
                )

        return Response(data)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.validated_data, status=201)


class SplitterAddressesListAPIView(ListAPIView):
    serializer_class = AddressSerializer
    parent_class = End3

    def get_queryset(self):
        addresses_ids = set(
            self.parent_class.objects.all()
                .select_related("address")
                .values_list("address", flat=True)
        )
        return Address.objects.filter(id__in=addresses_ids)


class BuildingsAddressesListAPIView(SplitterAddressesListAPIView):
    parent_class = HouseB
