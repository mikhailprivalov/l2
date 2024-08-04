import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import cash_registers.views as cash_register_views
from cash_registers.models import Shift


@login_required
def get_cash_registers(request):
    result = cash_register_views.get_cash_registers()
    return JsonResponse({"result": result})


@login_required
def open_shift(request):
    request_data = json.loads(request.body)
    check_shift = Shift.check_shift(request_data["cashRegisterId"], request.user.doctorprofile.id)
    if not check_shift["ok"]:
        return check_shift
    shift_data = cash_register_views.open_shift(request_data["cashRegisterId"], request.user.doctorprofile.id)
    return JsonResponse(shift_data)


@login_required
def close_shift(request):
    request_data = json.loads(request.body)
    result = cash_register_views.close_shift(request_data["cashRegisterId"], request.user.doctorprofile.id)
    return JsonResponse(result)


@login_required
def get_shift_data(request):
    result = cash_register_views.get_shift_data(request.user.doctorprofile.id)
    return JsonResponse(result)
