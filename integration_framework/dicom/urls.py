from django.urls import path
from . import views

urlpatterns = [
    path('get-meta-tags', views.get_meta_tags),
]
