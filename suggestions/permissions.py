"""
Permissões customizadas para o app de sugestões.
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permissão que permite apenas ao owner editar, leitura pública para outros."""

    def has_object_permission(self, request, view, obj):
        # Métodos seguros: permitir
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write apenas ao owner
        return obj.proposer == request.user


class CanApproveSuggestion(permissions.BasePermission):
    """Permissão para usuários que podem aprovar sugestões.

    Por padrão, staff (is_staff) ou usuário com permissão can_approve_suggestion.
    """

    def has_permission(self, request, view) -> bool:  # type: ignore[override]
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or user.has_perm("suggestions.can_approve_suggestion")
