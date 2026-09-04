from django.urls import path

from . import views

urlpatterns = [
    path('get-real-estates', views.get_real_estates),
    path('create-real-estate', views.create_real_estate),
    path('update-real-estate', views.update_real_estate),
    path('get-real-estate-owner', views.get_real_estate_owner),
    path('save-real-estate-owner', views.save_real_estate_owner),
    path('delete-real-estate-owner', views.delete_real_estate_owner),
    path('get-bank-receipts', views.get_bank_receipts),
    path('create-bank-receipt', views.create_bank_receipt),
    path('update-bank-receipt', views.update_bank_receipt),
    path('delete-bank-receipt', views.delete_bank_receipt),
    path('get-payment-types', views.get_payment_types),
    path('get-year-payment-types', views.get_year_payment_types),
    path('get-accounting-summary', views.get_accounting_summary),
    path('create-payment-type', views.create_payment_type),
    path('update-payment-type', views.update_payment_type),
    path('create-payment-type-rate', views.create_payment_type_rate),
    path('update-payment-type-rate', views.update_payment_type_rate),
    path('delete-payment-type-rate', views.delete_payment_type_rate),
    path('get-electricity-readings', views.get_electricity_readings),
    path('create-electricity-reading', views.create_electricity_reading),
    path('update-electricity-reading', views.update_electricity_reading),
    path('delete-electricity-reading', views.delete_electricity_reading),
]
