from django.urls import path

from . import views

urlpatterns = [
    path('all-analyzers', views.all_analyzers),
    path('manage-profile-analyzer', views.manage_profile_analyzer),
    path('status-analyzer', views.status_analyzer),
    path('restart-analyzer', views.restart_analyzer),
    path('status-systemctl', views.status_systemctl),
    path('analyzers-load-file', views.analyzers_load_file),
]
