from django.urls import path
from . import views

urlpatterns = [
    path('get-directions-for-mail-send', views.get_directions_for_mail_send),
]
