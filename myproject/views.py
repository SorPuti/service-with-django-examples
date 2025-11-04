import random
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import get_user_model
from rest_framework import serializers, permissions, generics, viewsets


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # expose only safe fields for profile editing
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "test_field"
        )
        read_only_fields = ("id",)



class UserProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the authenticated user's profile.

    GET returns the current user's public fields.
    PATCH allows partial updates to username, email, first_name and last_name.
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):  # type: ignore[override]
        return self.request.user


def test_view(request: HttpRequest):
    randomId = random.randint(1, 100)
    user = getattr(request, "user", None)
    return HttpResponse(f"Hello world from test view! Random ID: {randomId}, {type(user)}/{user}")


def index_view(request: HttpRequest):
    return HttpResponse("<h1>Welcome to MyProject</h1><p>This is the index page.</p>")