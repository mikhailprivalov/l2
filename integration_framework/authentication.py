from django.core.exceptions import ValidationError
from rest_framework import authentication
from rest_framework import exceptions

from api.models import Application


class TokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        if not token or not token.startswith('Bearer '):
            raise exceptions.AuthenticationFailed('No such token')
        token = token.replace('Bearer ', '')
        try:
            app = Application.objects.filter(active=True, key=token).first()
        except ValidationError:
            raise exceptions.AuthenticationFailed('No such token')
        if not app:
            raise exceptions.AuthenticationFailed('No such active APP with token')

        return app, None
