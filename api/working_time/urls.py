from django.urls import path

from api.transfer_document import views

urlpatterns = [
    path('get-columns', views.get_destination_source),
]
