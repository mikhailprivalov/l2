import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import cash_registers.views as cash_register_views


@login_required
def get_cash_registers(request):
    result = cash_register_views.get_cash_registers()
    return JsonResponse({"result": result})


@login_required
def open_shift(request):
    request_data = json.loads(request.body)
    shift_data = cash_register_views.open_shift(request_data["cashRegisterId"], request.user.doctorprofile.id)
    return JsonResponse(shift_data)


@login_required
def close_shift(request):
    result = cash_register_views.close_shift(request.user.doctorprofile.id)
    return JsonResponse(result)


@login_required
def get_shift_status(request):
    request_data = json.loads(request.body)
    result = cash_register_views.get_shift_status(request.user.doctorprofile.id, request_data["cashRegisterId"])
    return JsonResponse(result)
