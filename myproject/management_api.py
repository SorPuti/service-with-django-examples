from django.contrib.auth.models import Group, Permission
from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAdminUser


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "codename", "name", "content_type"]


class GroupSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(many=True, queryset=Permission.objects.all())

    class Meta:
        model = Group
        fields = ["id", "name", "permissions"]


class GroupViewSet(viewsets.ModelViewSet):
    """Admin API for managing groups."""

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminUser]


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list of permissions for admin tooling."""

    queryset = Permission.objects.select_related("content_type").all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAdminUser]


# Router-compatible urlpatterns: include the router.urls from this module
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"groups", GroupViewSet, basename="group")
router.register(r"permissions", PermissionViewSet, basename="permission")

urlpatterns = router.urls
