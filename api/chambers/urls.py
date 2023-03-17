from django.urls import path

from . import views

urlpatterns = [
    path('all-patients', views.get_list_patients),
    path('get-chambers', views.get_chambers),
    path('get-beds', views.get_beds),
    path('load-data-beds', views.load_data_beds),
]
