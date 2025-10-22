from django.urls import path
from . import views

urlpatterns = [
    path('get-med-protocols', views.get_med_protocols),
    path('get-pdf', views.get_pdf_protocol),
    path('put-state', views.result_accept_protocol),
]