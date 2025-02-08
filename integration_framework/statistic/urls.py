from django.urls import path
from . import views

urlpatterns = [
    path('get-statistic-research', views.get_statistic_research),
]
