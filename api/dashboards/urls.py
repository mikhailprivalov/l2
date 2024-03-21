from django.urls import path

from . import views

urlpatterns = [
    path('listdashboard', views.dashboard_list),
    path('dashboard-charts', views.dashboard_charts),
    path('cash-reister', views.cash_register),

]
