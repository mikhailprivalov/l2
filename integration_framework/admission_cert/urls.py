from django.urls import path
from . import views

urlpatterns = [
    path('get-med-protocols', views.get_med_protocols),
    path('get-result-protocol', views.get_result_protocol),
    path('put-state', views.result_accept_protocol),
]