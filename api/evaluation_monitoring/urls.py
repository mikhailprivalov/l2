from django.urls import path

from . import views

urlpatterns = [
    path('hospitals', views.hospitals),
    path('load', views.load),
    path('add_result', views.add_result),
]
