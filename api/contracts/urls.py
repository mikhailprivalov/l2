from django.urls import path

from . import views

urlpatterns = [
    path('create-new-billing', views.create_new_billing),
    path('get-research-for-billing', views.get_research_for_billing),
    path('get-billings', views.get_billings),
    path('get-billing', views.get_billing),
]
