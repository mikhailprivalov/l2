from django.urls import path

from api.transfer_document import views

urlpatterns = [
    path('get-destination-source', views.get_destination_source),
    path('get-card-accept', views.get_cards_to_accept),
    path('get-card-send', views.get_cards_to_send),
    path('get-card-by-number', views.get_card_by_number),
    path('send-document', views.send_document),
    path('accept-document', views.accept_document),
]
