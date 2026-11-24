from django.urls import path

from . import views

urlpatterns = [
    path('add-med-record', views.add_med_record),
    path('add-med-record-template', views.add_med_record_template),
]
