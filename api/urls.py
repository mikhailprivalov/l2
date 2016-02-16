from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^send$', views.send),  #  SYSMEX
    url(r'^results$', views.results), #  SAPPHIRE
    url(r'^get_order$', views.get_order),
]
