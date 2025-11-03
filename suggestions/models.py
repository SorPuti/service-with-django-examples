"""
Modelos para o sistema de sugestões.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Suggestion(models.Model):
    """Modelo principal que representa uma sugestão submetida por um usuário.

    Campos principais:
    - title: título curto da sugestão
    - description: descrição detalhada
    - proposer: usuário que submeteu
    - status: fluxo de aprovação (pending, approved, rejected)
    - is_public: se será visível publicamente antes da aprovação
    - approved_by / approved_at: controle de quem aprovou e quando
    - votes_count: contador cache para consultas rápidas
    """

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendente"),
        (STATUS_APPROVED, "Aprovada"),
        (STATUS_REJECTED, "Rejeitada"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    proposer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="suggestions"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    is_public = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_suggestions",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    votes_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("can_approve_suggestion", "Can approve suggestions"),
        ]

    def approve(self, user):
        """Marcar sugestão como aprovada por um usuário.

        Atualiza campos de auditoria e status.
        """
        self.status = self.STATUS_APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

    def reject(self, user):
        """Marcar sugestão como rejeitada."""
        self.status = self.STATUS_REJECTED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

    def __str__(self):
        return f"{self.title} ({self.status})"


class SuggestionComment(models.Model):
    """Comentários em uma sugestão. Permite discussões antes/depois da aprovação."""

    suggestion = models.ForeignKey(Suggestion, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.suggestion.pk}"


class SuggestionVote(models.Model):
    """Votos para uma sugestão. Cada usuário pode votar uma vez (unique constraint)."""

    suggestion = models.ForeignKey(Suggestion, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("suggestion", "user")

    def __str__(self):
        return f"Vote by {self.user} on {self.suggestion.pk}"


class SuggestionAuditLog(models.Model):
    """Registro de auditoria para operações críticas sobre Suggestion.

    Armazena eventos como create/update/approve/reject com payload mínimo.
    """

    suggestion = models.ForeignKey(Suggestion, on_delete=models.CASCADE, related_name="audit_logs")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=50)
    detail = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Audit {self.action} on {self.suggestion.pk} at {self.timestamp}"
