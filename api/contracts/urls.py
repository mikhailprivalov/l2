from django.urls import path

from . import views

urlpatterns = [
    path('get-subgroups-all', views.get_subgroups_all),
]
