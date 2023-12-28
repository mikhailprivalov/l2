from functools import wraps
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import authentication
from rest_framework import exceptions

from api.models import Application
from integration_framework.models import IndividualAuth


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


class IndividualAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        if not token or not token.startswith('Basic '):
            raise exceptions.AuthenticationFailed('No such token')
        token = token.replace('Basic ', '')
        try:
            individual: IndividualAuth = IndividualAuth.objects.filter(token=token, is_confirmed=True).first()
        except ValidationError:
            raise exceptions.AuthenticationFailed('No such token')
        if not individual:
            raise exceptions.AuthenticationFailed('No such active APP with token')

        individual.last_activity = timezone.now()
        individual.save(update_fields=['last_activity'])

        return individual, None


def can_use_schedule_only(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not hasattr(request.user, 'can_access_schedule'):
            raise exceptions.AuthenticationFailed('Invalid auth token')
        app: Application = request.user
        if not app.active:
            raise exceptions.AuthenticationFailed('The token is expired')
        if not app.can_access_schedule:
            raise exceptions.AuthenticationFailed("The token does not have access to the schedule")
        return function(request, *args, **kwargs)

    return wrap
