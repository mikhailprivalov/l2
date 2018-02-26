from django.urls import path
from . import views
from directory import views as d_views

urlpatterns = [
    path('menu', views.menu),
    path('researches', views.researches),
    path('researches-descriptive', views.researches_descriptive),
    path('researches/tune', views.researches_tune),
    path('researches/get_details', d_views.researches_get_details),
    path('tubes', views.tubes),
    path('directions_group', views.directions_group),
    path('uets', views.uets),
    path('with', views.onlywith),
    path('refs', views.refs),
]
