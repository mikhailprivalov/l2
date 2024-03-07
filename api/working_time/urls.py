from django.urls import path
from api.working_time import views

urlpatterns = [
    path('get-departments', views.get_departments),
]
