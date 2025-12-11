from rest_framework.response import Response
from rest_framework.decorators import api_view
from api.models import Application
from directions.models import Napravleniya
import simplejson as json
from slog.models import Log


@api_view(['POST'])
def data_by_direction(request):
    token = request.META.get("HTTP_AUTHORIZATION")
    token = token.replace("Bearer ", "")
    if not token:
        return Response({"message": "token is empty"})
    token_is_not_valid = False
    app = None
    try:
        app = Application.objects.filter(active=True, key=token).first()
        if not app:
            token_is_not_valid = True
    except:
        token_is_not_valid = True

    if token_is_not_valid:
        return Response({"message": "token is not valid"})

    data = json.loads(request.body)
    direction_id = data.get("directionId")

    direction = Napravleniya.objects.filter(pk=direction_id).first()

    return Response({"direction": direction.pk})
