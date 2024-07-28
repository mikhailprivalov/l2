import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


@login_required
def open_shift(request):
    request_data = json.loads(request.body)
    print(request_data)
    data = {"cashRegisterId": 1, "title": "fdfd", "shiftId": 1}
    print('Мы тут смену решили открывтаь')
    return JsonResponse({"data": data})


@login_required
def close_shift(request):
    request_data = json.loads(request.body)
    data = {"cashRegisterId": None, "title": "", "shiftId": None}
    print('Мы тут смену решили закрывтаь')
    return JsonResponse({"data": data})
