from django.urls import path

from . import views

urlpatterns = [
    path('search-indicator', views.search_indicator),
    path('save-indicator-value', views.save_indicator_value),
]
