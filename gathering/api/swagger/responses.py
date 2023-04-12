from rest_framework import serializers


class NodesSwaggerSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    shape = serializers.ChoiceField(choices=["dot"])
    color = serializers.CharField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class EdgesSwaggerSerializer(serializers.Serializer):
    _from = serializers.CharField()
    to = serializers.CharField()
    title = serializers.CharField()
    value = serializers.IntegerField()
    color = serializers.CharField()

    def __init__(self, **kwargs):
        """
        Меняем поле `_from` на `from`
        """
        super().__init__(**kwargs)
        if self._declared_fields.get("_from"):
            self._declared_fields["from"] = self._declared_fields["_from"]
            del self._declared_fields["_from"]

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class MacTracerouteSwaggerSerializer(serializers.Serializer):
    nodes = NodesSwaggerSerializer(many=True)
    edges = EdgesSwaggerSerializer(many=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
