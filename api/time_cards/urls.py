from django.urls import path
from . import views


urlpatterns = [
    path('load-department', views.load_department),
    path('update-department', views.update_department),
    path('load-person', views.load_person),
    path('update-person', views.update_perosn),
]
