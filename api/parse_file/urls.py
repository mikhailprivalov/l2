from django.urls import path

from . import views

urlpatterns = [
    path('loadfile', views.load_file),
    path('loadcsv', views.load_csv),
    path('loadequipment', views.load_equipment),
    path('upload-file', views.upload_file),
    path('get-allowed-forms', views.get_allowed_forms_file),
]
