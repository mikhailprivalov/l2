from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from clients.models import Card
from directions.models import Issledovaniya, Napravleniya
from laboratory.decorators import group_required
import simplejson as json


@login_required
@group_required("Врач стационара")
def load(request):
    data = json.loads(request.body)
    result = {"ok": False, "message": "Нет данных", "data": {}}
    pk = int(data["pk"])
    if pk >= 4600000000000:
        pk -= 4600000000000
        pk //= 10
    for i in Issledovaniya.objects.filter(napravleniye__pk=pk, research__is_hospital=True):
        direction: Napravleniya = i.napravleniye
        card: Card = direction.client
        result["ok"] = True
        result["message"] = ""
        result["data"] = {
            "direction": direction.pk,
            "patient": {
                "fio_age": card.individual.fio(full=True),
                "card": card.number_with_type(),
                "base": card.base_id,
                "card_pk": card.pk,
                "individual_pk": card.individual_id,
            }
        }
        break
    return JsonResponse(result)
