from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SuggestionViewSet,
    SuggestionCommentViewSet,
    SuggestionVoteViewSet,
    SuggestionAuditLogViewSet,
)

router = DefaultRouter()
router.register(r"suggestions", SuggestionViewSet, basename="suggestion")
router.register(r"comments", SuggestionCommentViewSet, basename="suggestioncomment")
router.register(r"votes", SuggestionVoteViewSet, basename="suggestionvote")
router.register(r"audit", SuggestionAuditLogViewSet, basename="suggestionaudit")

urlpatterns = [
    path("", include(router.urls)),
]
