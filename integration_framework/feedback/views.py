from rest_framework.response import Response
from directions.models import Napravleniya

from rest_framework.decorators import api_view
import simplejson as json


@api_view(['POST'])
def save_ecp_directions_number(request):
    body = json.loads(request.body)
    direction_id = body.get("direction")
    ecp_direction_id = body.get("evnDirectionId")
    n = Napravleniya.objects.get(pk=direction_id)
    n.ecp_direction_number = ecp_direction_id
    n.result_rmis_send = True
    n.save()
    return Response({"ok": True, "ecpDirectionId": ecp_direction_id})
