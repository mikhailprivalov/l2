from django.urls import path

from . import views

urlpatterns = [
    path('district-create', views.district_create),
    path('districts-load', views.districts_load),
    path('district-edit', views.district_edit),
]
