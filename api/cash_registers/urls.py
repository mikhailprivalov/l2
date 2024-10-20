from django.urls import path
from . import views

urlpatterns = [
    path('get-cash-registers', views.get_cash_registers),
    path('open-shift', views.open_shift),
    path('close-shift', views.close_shift),
    path('get-shift-data', views.get_shift_data),
    path('get-services-coasts', views.get_services_coasts),
    path('payment', views.payment),
    path('get-cheque-data', views.get_cheque_data),
]
