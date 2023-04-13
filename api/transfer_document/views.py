import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from clients.models import Card, CardMovementRoom
from podrazdeleniya.models import Room


@login_required
def get_destination_source(request):
    request_data = json.loads(request.body)
    doc = request.user.doctorprofile
    all_rooms = [{"id": -1, "label": "не выбрано"}, *[{"id": i.pk, "label": i.title} for i in Room.objects.all()]]
    source_rooms = Room.objects.filter(id__in=[x.pk for x in doc.room_access.all()])
    rooms = [{"id": -1, "label": "не выбрано", "isCardStorage": False}, *[{"id": i.pk, "label": i.title, "isCardStorage": i.is_card_storage} for i in source_rooms]]
    if request_data.get('value') == "Отправить":
        sources = rooms
        destination = all_rooms
    else:
        destination = rooms
        sources = [{"id": -1, "label": "не выбрано", "isCardStorage": False}, *CardMovementRoom.get_await_accept([i["id"] for i in rooms])]
    return JsonResponse({"sources": sources, "destinations": destination})


@login_required
def get_cards_to_accept(request):
    request_data = json.loads(request.body)
    room_from_id = request_data.get('roomOutId')
    room_to_id = request_data.get('roomInId')
    cards = CardMovementRoom.get_accept_card(room_from_id, room_to_id)
    data = [{"id": i.id, "number_p": i.number_poliklinika, "fio": i.get_fio_w_card(), "room": i.room_location.title, "checked": False} for i in cards]
    return JsonResponse({"cardToAccept": data})


@login_required
def get_cards_to_send(request):
    request_data = json.loads(request.body)
    room_id = request_data.get('value')
    data = []
    if int(room_id) != -1:
        room_obj = Room.objects.filter(id=room_id).first()
        if not room_obj.is_card_storage:
            cards_obj = Card.objects.filter(room_location_id=room_id)
            card_movement = CardMovementRoom.objects.values_list("card_id", flat=True).filter(room_in_id=room_id, doc_who_received=None, date_received=None)
            cards = cards_obj.all().exclude(id__in=card_movement)
            data = [{"id": i.id, "number_p": i.number_poliklinika, "fio": i.get_fio_w_card(), "room": i.room_location.title, "checked": False} for i in cards]
    return JsonResponse({"cardToSend": data})


@login_required
def get_card_by_number(request):
    request_data = json.loads(request.body)
    number_poliklinika = request_data.get('value')
    card_data = Card.objects.filter(number_poliklinika=number_poliklinika).first()
    data = {}
    if card_data:
        data = {"id": card_data.id, "number_p": card_data.number_poliklinika, "fio": card_data.get_fio_w_card(), "room": card_data.room_location.title, "checked": True}
    return JsonResponse({"card": data})


@login_required
def send_document(request):
    request_data = json.loads(request.body)
    room_out_id = request_data.get('source')
    room_in_id = request_data.get('destination')
    doc_who_issued_id = request.user.doctorprofile.id
    cards = request_data.get('cards')
    CardMovementRoom.transfer_send(cards, room_out_id, room_in_id, doc_who_issued_id)
    return JsonResponse({"data": "ok"})


@login_required
def accept_document(request):
    request_data = json.loads(request.body)
    room_out_id = request_data.get('source')
    room_in_id = request_data.get('destination')
    doc_who_issued_id = request.user.doctorprofile.id
    cards = request_data.get('cards')
    CardMovementRoom.transfer_accept(cards, room_out_id, room_in_id, doc_who_issued_id)
    return JsonResponse({"data": "ok"})
