from django.urls import path

from . import views

urlpatterns = [
    path('loadculture', views.load_culture),
    path('saveculture', views.save_culture)
]
