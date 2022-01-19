from django.urls import path

from . import views

urlpatterns = [
    path('phones-transfers', views.get_phones_transfers),
]
