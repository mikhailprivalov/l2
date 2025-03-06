from django.urls import path
from . import views

urlpatterns = [
    path('save-ecp-directions-number', views.save_ecp_directions_number),
]