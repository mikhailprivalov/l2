from django.urls import path

from . import views

urlpatterns = [
    path('external-performer', views.external_performer),
]
