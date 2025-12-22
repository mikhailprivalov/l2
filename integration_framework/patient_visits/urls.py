from django.urls import path
from . import views

urlpatterns = [
    path('data-by-direction', views.data_by_direction),
    path('result-sent-rmis-direction', views.result_rmis_sent_direction),
]
