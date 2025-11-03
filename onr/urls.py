from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OnrModelViewSet

router = DefaultRouter()
router.register(r"onr-models", OnrModelViewSet, basename="onrmodel")

urlpatterns = [
    path("", include(router.urls)),
]
