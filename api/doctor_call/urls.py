from django.urls import path

from . import views

urlpatterns = [
    path('create', views.create),
    path('actual-rows', views.actual_rows),
    path('cancel-row', views.cancel_row),
    path('search', views.search),
    path('change-status', views.change_status),
    path('change-executor', views.change_executor),
]
