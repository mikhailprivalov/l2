from django.urls import path

from . import views

urlpatterns = [
    path('result/next', views.next_result_direction),
    path('direction/data', views.direction_data),
]
