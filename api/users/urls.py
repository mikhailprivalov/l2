from django.urls import path

from . import views

urlpatterns = [
    path('auth', views.auth),
    path('change-password', views.change_password),
    path('set-new-email', views.set_new_email),
    path('loose-password', views.loose_password),
    path('generate-totp-code', views.generate_totp_code),
    path('set-totp', views.set_totp),
    path('disable-totp', views.disable_totp),
]
