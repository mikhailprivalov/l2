import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


@login_required
def open_shift(request):
    request_data = json.loads(request.body)
    data = {"cashRegisterId": 1, "title": "fdfd", "shiftId": 1 }
    print('Мы тут смену решили открывтаь')
    return JsonResponse({"data": data})
