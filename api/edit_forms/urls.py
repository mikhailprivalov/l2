from django.urls import path

from . import views

urlpatterns = [
    path('markup', views.form_markup),
    path('save', views.form_save),
    path('objects/get-by-id', views.object_by_id),
    path('objects/search', views.objects_search),
]
