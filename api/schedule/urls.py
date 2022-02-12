from django.urls import path

from . import views

urlpatterns = [
    path('days', views.days),
    path('details', views.details),
    path('save', views.save),
    path('save-resource', views.save_resource),
    path('search-resource', views.search_resource),
    path('get-first-user-resource', views.get_first_user_resource),
    path('create-slots', views.create_slots),
    path('available-slots', views.available_slots),
]
