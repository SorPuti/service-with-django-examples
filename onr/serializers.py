from rest_framework import serializers
from .models import OnrModel


class OnrModelSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = OnrModel
        fields = [
            "id",
            "name",
            "code",
            "description",
            "owner",
            "status",
            "version",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]
