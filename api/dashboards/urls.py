from django.urls import path

from . import views

urlpatterns = [
    path('dashboard', views.dashboard),
    path('dashboard-charts', views.dashboard_charts),
]
