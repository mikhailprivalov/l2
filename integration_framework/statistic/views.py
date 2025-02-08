import base64
import simplejson as json
from django.http import JsonResponse, HttpRequest
from rest_framework.decorators import api_view
from statistic.views import statistic_xls
from rest_framework.response import Response


@api_view(["POST"])
def get_statistic_research(request):
    data = json.loads(request.body)
    hospital = data.get('hospital')
    date_start = data.get('date-start')
    date_end = data.get('date-end')
    if not date_start or not date_end:
        return JsonResponse({"message": 'Неверная дата'})
    if not hospital:
        return JsonResponse({"message": 'Неверно значение МО'})

    params = {"type": "message-ticket", "hospital": -1, "date-start": date_start, "date-end": date_end}
    request_obj = HttpRequest()
    request_obj.GET = params
    request_obj.user = request.user

    xlsx_content = statistic_xls(request_obj)
    result_b64 = base64.b64encode(xlsx_content.content).decode("utf-8")
    return Response({"data": result_b64})
