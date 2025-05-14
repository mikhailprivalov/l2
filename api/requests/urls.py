from django.urls import path

from . import views

urlpatterns = [
    path('list', views.get_requests),
    path('equipment', views.get_equipment_list),
    path('images', views.get_request_images),
    path('create', views.create_request),
]
