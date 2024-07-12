from django.urls import path

from . import views

urlpatterns = [
    path('create-billing', views.create_billing),
    path('update-billing', views.update_billing),
    path('confirm-billing', views.confirm_billing),
    path('cancel-billing', views.cancel_billing),
    path('get-billings', views.get_billings),
    path('get-billing', views.get_billing),
    path('get-hospital-prices', views.get_hospital_prices),
    path('price/delete-all-coasts', views.get_hospital_prices),
]
