import base64
import simplejson as json
from django.http import HttpRequest
from rest_framework.decorators import api_view
from statistic.views import statistic_xls
from rest_framework.response import Response


@api_view(["POST"])
def get_statistic_research(request):
    data = json.loads(request.body)
    request_obj = HttpRequest()
    request_obj.GET = data
    if not request.user.unlimited_access:
        result = "Доступ запрещён"
    else:
        request_obj.user = request.user
        xlsx_content = statistic_xls(request_obj)
        result = base64.b64encode(xlsx_content.content).decode("utf-8")
    return Response({"data": result})
