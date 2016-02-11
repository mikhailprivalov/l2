from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^send$', views.send),
    url(r'^results$', views.results),
    url(r'^get_order$', views.get_order),
]
