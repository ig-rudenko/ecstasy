from rest_framework import serializers


class GetVlanDescQuerySerializer(serializers.Serializer):
    vlan = serializers.IntegerField(max_value=4096, min_value=1)


class TracerouteQuerySerializer(serializers.Serializer):
    mode = serializers.ChoiceField(
        choices=("vlan", "mac", "neighbors"),
        default="vlan",
        required=False,
        help_text="Traceroute mode.",
    )
    vlan = serializers.IntegerField(max_value=4096, min_value=1, required=False)
    mac = serializers.CharField(
        allow_blank=True,
        default="",
        required=False,
        trim_whitespace=True,
        help_text="MAC address filter.",
    )
    mac_vlan = serializers.IntegerField(max_value=4096, min_value=1, required=False)
    ep = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Show empty ports.",
    )
    ad = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Show admin down ports.",
    )
    double_check = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Check VLAN on both neighbor ports.",
    )
    graph_min_length = serializers.IntegerField(
        min_value=0,
        default=0,
        max_value=1024,
        required=False,
        help_text="Minimum node count in a graph component.",
    )
    nodes_only = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Show only network device nodes.",
    )
    device_name = serializers.CharField(
        allow_blank=True,
        default="",
        required=False,
        trim_whitespace=True,
        help_text="Device name filter.",
    )
    group = serializers.CharField(
        allow_blank=True,
        default="",
        required=False,
        trim_whitespace=True,
        help_text="Device group filter.",
    )

    def validate(self, attrs):
        """Validate required filter for selected traceroute mode."""
        mode = attrs.get("mode", "vlan")
        if mode == "vlan" and not attrs.get("vlan"):
            raise serializers.ValidationError({"vlan": "This field is required for VLAN traceroute."})
        if mode == "mac" and not attrs.get("mac"):
            raise serializers.ValidationError({"mac": "This field is required for MAC traceroute."})
        return attrs


VlanTracerouteQuerySerializer = TracerouteQuerySerializer
