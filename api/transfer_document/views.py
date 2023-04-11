import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from podrazdeleniya.models import Podrazdeleniya, Room
from slog.models import Log


@login_required
def get_destination_source(request):
    request_data = json.loads(request.body)
    doc = request.user.doctorprofile
    print(request_data)
    source_rooms = Room.objects.filter(id__in=[x.pk for x in doc.room_access.all()])
    rooms = [{ "id": -1, "label": 'не выбрано' }, *[{"id": i.pk, "label": i.title} for i in source_rooms]]
    destination = [{ "id": -1, "label": 'не выбрано' }]
    sources = [{ "id": -1, "label": 'не выбрано' }]
    if request_data.get('value') == "Отправить":
        sources = rooms
    else:
        destination = rooms

    return JsonResponse({"sources": sources, "destinations": destination})