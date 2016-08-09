from django.conf.urls import url
from . import views
from directory import views as d_views

urlpatterns = [
    url(r'^menu$', views.menu),
    url(r'^researches$', views.researches),
    url(r'^researches/tune$', views.researches_tune),
    url(r'^researches/get_details$', d_views.researches_get_details),
    url(r'^tubes', views.tubes),
    url(r'^directions_group', views.directions_group),
    url(r'^uets$', views.uets),
    url(r'^with$', views.onlywith),
]
