from django.urls import path

from . import views

urlpatterns = [
    path('all-patients', views.get_list_patients),
    path('get-chambers-and-bed', views.get_chambers_and_bed),
    # path('get-beds', views.get_beds),
    path('load-data-bed', views.load_data_bed),
]
