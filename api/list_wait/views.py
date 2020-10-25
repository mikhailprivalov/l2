from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import simplejson as json


@login_required
def create(request):
    request_data = json.loads(request.body)
    return JsonResponse({"ok": request_data})
