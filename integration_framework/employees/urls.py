from django.urls import path
from . import views

urlpatterns = [
    path('cash-register', views.cash_register),
    path('register-data', views.get_register_data),
]
