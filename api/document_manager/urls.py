from django.urls import path

from . import views

urlpatterns = [
    path('groups/list', views.groups_list),
    path('groups/update', views.groups_update),
    path('types/list', views.types_list),
    path('types/update', views.types_update),
    path('structure/details', views.structure_details),
    path('structure/update', views.structure_update),
]
