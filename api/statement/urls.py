from django.urls import path

from api.reports import views

urlpatterns = [
    path('select-tubes', views.select_tubes_statemen),
    path('save-tubes-statement', views.select_tubes_statement),
]
