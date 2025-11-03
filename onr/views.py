from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import OnrModel
from .serializers import OnrModelSerializer
from utils.query_builder import build_filters_from_params, sanitize_ordering
from rest_framework.decorators import action
from rest_framework.response import Response




class OnrModelViewSet(viewsets.ModelViewSet):
    """API endpoint for ONR models."""

    queryset = OnrModel.objects.all()
    serializer_class = OnrModelSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    allowed_filters = {
        "name": "name",
        "code": "code",
        "owner": "owner__id",
    }
    allowed_ordering = ["created_at", "updated_at"]

    def perform_create(self, serializer):
        # assign the requesting user as owner
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset().select_related("owner")
        params = {k: v for k, v in self.request.query_params.items()}
        q_obj, kwargs = build_filters_from_params(params, self.allowed_filters)
        qs = qs.filter(q_obj, **kwargs)
        ordering_param = self.request.query_params.get("ordering")
        ord_clean = sanitize_ordering(ordering_param, self.allowed_ordering)
        if ord_clean:
            qs = qs.order_by(ord_clean)
        return qs

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticatedOrReadOnly])
    def filters(self, request):
        return Response({
            "allowed_filters": list(self.allowed_filters.keys()),
            "allowed_ordering": self.allowed_ordering,
        })
