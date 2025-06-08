from django.urls import path

from . import views

urlpatterns = [
    path('types', views.get_types),
    path('orgs', views.get_orgs),
    path('users', views.get_users),
    path('logs', views.get_logs),
]
