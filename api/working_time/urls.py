from django.urls import path

from api.working_time import views

urlpatterns = [
    path('get-departments', views.get_departments),
    path('get-work-time', views.get_work_time),
    path('get-document', views.get_document),
    path('create-document', views.create_document),
]
