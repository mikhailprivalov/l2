from django.urls import path

from . import views

urlpatterns = [
    path('update_billing', views.update_billing),
    path('create-billing', views.create_billing),
    path('get-research-for-billing', views.get_research_for_billing),
]
