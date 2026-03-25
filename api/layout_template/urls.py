from django.urls import path

from . import views

urlpatterns = [
    path('list-treeselect', views.list_layout_template_treeselect),
]
