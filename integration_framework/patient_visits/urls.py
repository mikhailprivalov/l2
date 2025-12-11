from django.urls import path
from . import views

urlpatterns = [
    path('data-by-direction', views.data_by_direction),
]
