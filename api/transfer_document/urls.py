from django.urls import path

from api.transfer_document import views

urlpatterns = [
    path('get-destination-source', views.get_destination_source),
]
