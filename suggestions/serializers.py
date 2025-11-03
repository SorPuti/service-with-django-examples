"""
Serializers para a API de sugestões (Django REST Framework).
Comentários explicativos estão em Português para estudo.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Suggestion, SuggestionComment, SuggestionVote, SuggestionAuditLog


class SuggestionCommentSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source="author.username")

    class Meta:
        model = SuggestionComment
        fields = ("id", "suggestion", "author", "content", "created_at")
        read_only_fields = ("id", "author", "created_at")


class SuggestionSerializer(serializers.ModelSerializer):
    proposer = serializers.ReadOnlyField(source="proposer.username")
    comments = SuggestionCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Suggestion
        fields = (
            "id",
            "title",
            "description",
            "proposer",
            "status",
            "is_public",
            "votes_count",
            "comments",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "proposer", "status", "votes_count", "approved_by", "approved_at", "created_at", "updated_at")

    def create(self, validated_data):
        # O usuário atual será definido como proposer no viewset
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["proposer"] = request.user
        return super().create(validated_data)

User = get_user_model()

# Serializer for part. object 'User'
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")

class SuggestionVoteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    # serializer of context, for 'source' returned unique field value
    # user = serializers.ReadOnlyField(source="user.email")

    class Meta:
        model = SuggestionVote
        fields = ("id", "suggestion", "user", "created_at")
        read_only_fields = ("id", "user", "created_at")


class SuggestionAuditLogSerializer(serializers.ModelSerializer):
    actor = serializers.ReadOnlyField(source="actor.username")

    class Meta:
        model = SuggestionAuditLog
        fields = ("id", "suggestion", "actor", "action", "detail", "timestamp")
        read_only_fields = fields
