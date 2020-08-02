from django.urls import path

from . import views

urlpatterns = [
    path('result/next', views.next_result_direction),
    path('result/amd', views.get_dir_amd),
    path('result/n3', views.get_dir_n3),
    path('result/sendamd', views.result_amd_send),
    path('direction/data', views.direction_data),
    path('iss/data', views.issledovaniye_data),
    path('log', views.make_log),
]
