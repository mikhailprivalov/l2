from django.urls import path
from . import views

urlpatterns = [
    path('log', views.log),
    path('log/cleanup', views.log_cleanup),
    path('db', views.db),
    path('rmis/check', views.rmis_check),
    path('archive_cards', views.archive_without_directions),
    path('patients', views.patients_without_cards),
    path('sync/departments', views.sync_departments),
    path('sync/researches', views.sync_researches),
]
