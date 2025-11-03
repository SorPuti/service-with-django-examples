"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from rest_framework import routers
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from django.urls import include
from rest_framework.schemas import get_schema_view
from .views import UserProfileView


urlpatterns = [
    path("admin/", admin.site.urls),
    # Auth (dj-rest-auth + allauth)
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    # SimpleJWT token endpoints (use these from your clients)
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # API routes
    path("api/", include("onr.urls")),
    path("api/", include("suggestions.urls")),
    # Management API (groups / permissions)
    path("api/gestao/", include("myproject.management_api")),
    # Schema (machine-readable) to discover routes, paths and methods (OpenAPI/Core schema)
    path("api/schema/", get_schema_view(title="Service With Django API", description="API schema"), name="api-schema"),
    # User self-profile endpoint (view/update own profile)
    path("api/auth/me/", UserProfileView.as_view(), name="user-profile"),
    path("test/", views.test_view),  
    path("", views.index_view),
]
