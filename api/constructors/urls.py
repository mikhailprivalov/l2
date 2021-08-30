from django.urls import path
from . import views


urlpatterns = [
    path('hospital', views.hospital_fields),
]
