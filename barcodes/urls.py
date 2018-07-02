from django.urls import path
from . import views

urlpatterns = [
    path('tubes', views.tubes),
    path('login', views.login),
]
