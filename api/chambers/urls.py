from django.urls import path

from . import views

urlpatterns = [
    path('all-chambers', views.all_chambers),
]
