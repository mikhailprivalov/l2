from django.urls import path

from . import views

urlpatterns = [
    path('fractions', views.fractions),
    path('save-fsli', views.save_fsli),
]
