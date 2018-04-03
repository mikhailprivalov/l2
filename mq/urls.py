from django.urls import path

from . import views

urlpatterns = [
    path('object', views.get_object),
    path('directory', views.get_directory),
]
