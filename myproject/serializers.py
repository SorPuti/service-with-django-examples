from dj_rest_auth.registration.serializers import RegisterSerializer
from allauth.account import app_settings
from rest_framework import serializers


class CustomRegisterSerializer(RegisterSerializer):
    """
    Serializer atualizado para dj-rest-auth + django-allauth
    """

    # Campos obrigatórios conforme SIGNUP_FIELDS
    username = serializers.CharField(
        required=app_settings.SIGNUP_FIELDS.get('username', {}).get('required', True)
    )
    email = serializers.EmailField(
        required=app_settings.SIGNUP_FIELDS.get('email', {}).get('required', True)
    )

    def get_cleaned_data(self):
        """
        Retorna os dados limpos para criar o usuário.
        """
        data = super().get_cleaned_data()
        data['username'] = self.validated_data.get('username', '')
        data['email'] = self.validated_data.get('email', '')
        data['password1'] = self.validated_data.get('password1', '')
        data['password2'] = self.validated_data.get('password2', '')
        return data
