from django.urls import path
from . import views

urlpatterns = [
    path('get-cash-registers', views.get_cash_registers),
    path('open-shift', views.open_shift),
    path('close-shift', views.close_shift),
    path('get-shift-status', views.get_shift_status),
]
