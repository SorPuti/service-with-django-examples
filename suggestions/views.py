"""
Views (DRF ViewSets) para o app de sugestões.
Inclui ações customizadas: approve/reject e endpoints para votar/comentar.
"""
from django.contrib.auth.models import AnonymousUser
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q

from .models import Suggestion, SuggestionComment, SuggestionVote, SuggestionAuditLog
from .serializers import (
    SuggestionSerializer,
    SuggestionCommentSerializer,
    SuggestionVoteSerializer,
    SuggestionAuditLogSerializer,
)
from .permissions import IsOwnerOrReadOnly, CanApproveSuggestion
from myproject.drf_permissions import RequireGroupOrPermission
from utils.query_builder import build_filters_from_params, build_search_q, sanitize_ordering


class SuggestionViewSet(viewsets.ModelViewSet):
    """ViewSet principal para CRUD de sugestões."""

    queryset = Suggestion.objects.all()
    serializer_class = SuggestionSerializer
    # Permissions: read allowed to anonymous (read-only), write requires authentication;
    # object-level edits are allowed only for owners. Approve/reject use RequireGroupOrPermission
    permission_classes = [IsOwnerOrReadOnly, IsAuthenticatedOrReadOnly]
    required_groups_map = {"approve": ["approvers"], "reject": ["approvers"]}
    required_permissions_map = {
        "approve": ["suggestions.can_approve_suggestion"],
        "reject": ["suggestions.can_approve_suggestion"],
    }
    # Allowed filters mapping: client param -> model lookup
    allowed_filters = {
        "id": "id",
        "status": "status",
        "proposer": "proposer__id",
        "is_public": "is_public",
        "proposer_username": "proposer__username",
    }
    # Allowed ordering fields (without -)
    allowed_ordering = ["created_at", "votes_count", "approved_at"]
    # Searchable fields for `q` parameter
    searchable_fields = ["title", "description"]
    # Usamos filtros simples via query params (para evitar dependência de django-filter)
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "votes_count", "approved_at"]

    def perform_create(self, serializer):
        if isinstance(self.request.user, AnonymousUser):
            return
        serializer.save(proposer=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset().select_related("proposer")
        params = {k: v for k, v in self.request.query_params.items()}

        q_obj, kwargs = build_filters_from_params(params, self.allowed_filters)
        qs = qs.filter(q_obj, **kwargs)

        # Visibility rules:
        # - anonymous users only see public suggestions
        # - authenticated users see public suggestions and their own (even if not public)
        user = getattr(self.request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            qs = qs.filter(is_public=True)
        else:
            # non-staff users see public OR their own suggestions; staff sees all
            if not getattr(user, "is_staff", False):
                qs = qs.filter(Q(is_public=True) | Q(proposer=user))

        # search q param
        q_text = self.request.query_params.get("q")
        if q_text:
            search_q = build_search_q(q_text, self.searchable_fields)
            qs = qs.filter(search_q)

        # ordering
        ordering_param = self.request.query_params.get("ordering")
        ord_clean = sanitize_ordering(ordering_param, self.allowed_ordering)
        if ord_clean:
            qs = qs.order_by(ord_clean)

        return qs

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticatedOrReadOnly])
    def filters(self, request):
        """Endpoint de descoberta: retorna os filtros e query params aceitos por esse recurso."""
        return Response(
            {
                "allowed_filters": list(self.allowed_filters.keys()),
                "allowed_ordering": self.allowed_ordering,
                "searchable_fields": self.searchable_fields,
                "notes": "Use parameter 'q' to full-text icontains search on searchable_fields. Use 'ordering' for ordering (prefix with - for desc).",
            }
        )

    @action(detail=True, methods=["post"], permission_classes=[RequireGroupOrPermission])
    def approve(self, request, pk=None):
        suggestion = self.get_object()
        suggestion.approve(request.user)
        # registrar auditoria
        SuggestionAuditLog.objects.create(
            suggestion=suggestion, actor=request.user, action="approve", detail={}
        )
        return Response({"status": "approved"})

    @action(detail=True, methods=["post"], permission_classes=[RequireGroupOrPermission])
    def reject(self, request, pk=None):
        suggestion = self.get_object()
        suggestion.reject(request.user)
        SuggestionAuditLog.objects.create(
            suggestion=suggestion, actor=request.user, action="reject", detail={}
        )
        return Response({"status": "rejected"})


class SuggestionCommentViewSet(viewsets.ModelViewSet):
    queryset = SuggestionComment.objects.all()
    serializer_class = SuggestionCommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class SuggestionVoteViewSet(viewsets.ModelViewSet):
    queryset = SuggestionVote.objects.all()
    serializer_class = SuggestionVoteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        # criar voto e atualizar contador de forma segura
        suggestion_id = request.data.get("suggestion")
        if not suggestion_id:
            return Response({"detail": "suggestion required"}, status=status.HTTP_400_BAD_REQUEST)
        suggestion = Suggestion.objects.filter(id=suggestion_id).first()
        if not suggestion:
            return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)
        # garantir unicidade
        vote, created = SuggestionVote.objects.get_or_create(suggestion=suggestion, user=request.user)
        if created:
            suggestion.votes_count = suggestion.votes_count + 1
            suggestion.save(update_fields=["votes_count"])
        serializer = self.get_serializer(vote)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SuggestionAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SuggestionAuditLog.objects.all()
    serializer_class = SuggestionAuditLogSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
