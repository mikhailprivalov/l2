from django.urls import path

from api.statement import views

urlpatterns = [
    path('select-tubes', views.select_tubes_statement),
    path('save-tubes-statement', views.save_tubes_statement),
    path('show-history', views.show_history),
]
