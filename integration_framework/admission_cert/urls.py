from django.urls import path
from . import views

urlpatterns = [
    path('get-med-protocols', views.get_med_protocols),
]