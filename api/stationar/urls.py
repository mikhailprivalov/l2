from django.urls import path

from . import views

urlpatterns = [
    path('load', views.load),
    path('counts', views.counts),
    path('hosp-services-by-type', views.hosp_services_by_type),
    path('make-service', views.make_service),
    path('directions-by-key', views.directions_by_key),
    path('aggregate-laboratory', views.aggregate_laboratory),
    path('aggregate-desc', views.aggregate_desc),
    path('aggregate-tadp', views.aggregate_tadp),
    path('change-department', views.change_department),
    path('get-assignments', views.aggregate_assignments),
]
