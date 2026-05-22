from rest_framework import serializers


class NodesSwaggerSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()  # type: ignore
    shape = serializers.ChoiceField(choices=["dot"])
    color = serializers.CharField()
    title = serializers.CharField(required=False)


class EdgesSwaggerSerializer(serializers.Serializer):
    _from = serializers.CharField()
    to = serializers.CharField()
    title = serializers.DictField(help_text="Structured tooltip payload object.")
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
