from rest_framework.serializers import CharField, ListSerializer

ServicesType = ListSerializer[CharField]
