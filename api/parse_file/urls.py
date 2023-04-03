from django.urls import path

from . import views

urlpatterns = [
    path('loadfile', views.load_file),
    path('loadcsv', views.load_csv),
]
