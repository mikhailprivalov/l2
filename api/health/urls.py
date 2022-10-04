from django.urls import path

from . import views

urlpatterns = [
    path('log/stats', views.log_stats),
    path('archive-cards/stats', views.archive_cards_stats),
    path('patients/stats', views.patients_stats),
    path('log/cleanup', views.log_cleanup),
    path('archive-cards/cleanup', views.archive_cards_cleanup),
    path('patients/cleanup', views.patients_cleanup),
]
