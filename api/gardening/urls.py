from django.urls import path

from . import views

urlpatterns = [
    path('get-real-estates', views.get_real_estates),
    path('create-real-estate', views.create_real_estate),
    path('get-payment-types', views.get_payment_types),
    path('create-payment-type', views.create_payment_type),
    path('update-payment-type', views.update_payment_type),
    path('create-payment-type-rate', views.create_payment_type_rate),
    path('update-payment-type-rate', views.update_payment_type_rate),
    path('delete-payment-type-rate', views.delete_payment_type_rate),
]
