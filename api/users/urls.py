from django.urls import path

from . import views

urlpatterns = [
    path('auth', views.auth),
    path('change-password', views.change_password),
    path('set-new-email', views.set_new_email),
]
