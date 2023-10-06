from django.urls import path

from . import views

urlpatterns = [
    path('search', views.search),
    path('hosp-services-by-type', views.hosp_services_by_type),
    path('make-service', views.make_service),
    path('directions-by-key', views.directions_by_key),
    path('aggregate', views.aggregate),
]
