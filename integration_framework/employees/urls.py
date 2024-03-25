from django.urls import path
from . import views

urlpatterns = [
    path('cash-register', views.cash_register),
]
