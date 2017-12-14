from django.urls import path

from . import views

urlpatterns = [
    path('send', views.send),
    path('endpoint', views.endpoint),
    path('departments', views.departments)
]
