from django.contrib import admin
from .models import Suggestion, SuggestionComment, SuggestionVote, SuggestionAuditLog


@admin.action(description="Marcar selecionadas como aprovadas")
def approve_suggestions(modeladmin, request, queryset):
    for obj in queryset:
        obj.approve(request.user)


@admin.action(description="Marcar selecionadas como rejeitadas")
def reject_suggestions(modeladmin, request, queryset):
    for obj in queryset:
        obj.reject(request.user)


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "proposer", "status", "votes_count", "created_at")
    list_filter = ("status", "is_public", "created_at")
    search_fields = ("title", "description", "proposer__username")
    actions = [approve_suggestions, reject_suggestions]


@admin.register(SuggestionComment)
class SuggestionCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "suggestion", "author", "created_at")
    search_fields = ("content", "author__username")


@admin.register(SuggestionVote)
class SuggestionVoteAdmin(admin.ModelAdmin):
    list_display = ("id", "suggestion", "user", "created_at")


@admin.register(SuggestionAuditLog)
class SuggestionAuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "suggestion", "action", "actor", "timestamp")
    readonly_fields = ("suggestion", "actor", "action", "detail", "timestamp")
