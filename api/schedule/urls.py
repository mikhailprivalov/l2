from django.urls import path

from . import views

urlpatterns = [
    path('days', views.days),
    path('details', views.details),
    path('save', views.save),
]
