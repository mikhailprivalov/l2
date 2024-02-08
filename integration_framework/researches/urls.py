from django.urls import path
from . import views

urlpatterns = [
    path('get-confirm-sign-research', views.get_confirm_sign_research),
]
