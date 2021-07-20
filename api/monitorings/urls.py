from django.urls import path

from . import views

urlpatterns = [
    path('search', views.search),
    path('history', views.history),
    path('filexlsx', views.filexlsx),
]
