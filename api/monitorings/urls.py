from django.urls import path

from . import views

urlpatterns = [
    path('search', views.search),
    path('history', views.history),
    path('filexlsx', views.filexlsx),
    path('dashboard', views.get_dashboard),
]
