from rest_framework.generics import ListCreateAPIView, ListAPIView
from rest_framework.response import Response

from .serializers import CreateTechDataSerializer, AddressSerializer
from ..models import OLTState, End3, Address, HouseB


class TechDataListCreateAPIView(ListCreateAPIView):
    queryset = OLTState

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateTechDataSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.validated_data)
        return Response(serializer.validated_data, status=201, headers=headers)


class SplitterAddressesListAPIView(ListAPIView):
    serializer_class = AddressSerializer
    parent_class = End3

    def get_queryset(self):
        addresses_ids = set(
            self.parent_class.objects.all().select_related("address").values_list("address", flat=True)
        )
        return Address.objects.filter(id__in=addresses_ids)


class BuildingsAddressesListAPIView(SplitterAddressesListAPIView):
    parent_class = HouseB
