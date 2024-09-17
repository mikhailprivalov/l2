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
    if check_shift["ok"]:
        result = cash_register_views.open_shift(request_data["cashRegisterId"], request.user.doctorprofile.id)
    else:
        result = check_shift
    return JsonResponse(result)


@login_required
def close_shift(request):
    request_data = json.loads(request.body)
    result = cash_register_views.close_shift(request_data["cashRegisterId"], request.user.doctorprofile.id)
    return JsonResponse(result)


@login_required
def get_shift_data(request):
    result = cash_register_views.get_shift_data(request.user.doctorprofile.id)
    return JsonResponse(result)


@login_required
def get_services_coasts(request):
    request_data = json.loads(request.body)
    # result = cash_register_views.get_service_coasts(request_data["serviceIds"])
    result = {"coasts": [], "serviceWithoutCoast": False}
    return JsonResponse(result)


@login_required
def payment(request):
    request_data = json.loads(request.body)
    shift_id = request_data["shiftId"]
    coasts = request_data["serviceCoasts"]
    total_coast = request_data["totalCoast"]
    cash = request_data["cash"]
    received_cash = request_data["receivedCash"]
    electronic = request_data["electronic"]
    card_id = request_data["cardId"]
    result = cash_register_views.payment(shift_id, coasts, total_coast, cash, received_cash, electronic, card_id)
    return JsonResponse(result)


@login_required
def get_cheque_data(request):
    request_data = json.loads(request.body)
    result = cash_register_views.get_cheque_data(request_data["chequeId"])
    return JsonResponse(result)
