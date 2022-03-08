from django.urls import path

from . import views

urlpatterns = [
    path('dashboard', views.get_dashboard),
]
