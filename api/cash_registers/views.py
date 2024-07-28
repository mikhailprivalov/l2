import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from cash_registers.models import CashRegister, Shift


@login_required
def get_cash_registers(request):
    result = CashRegister.get_cash_registers()
    return JsonResponse({"result": result})


@login_required
def open_shift(request):
    request_data = json.loads(request.body)
    new_shift = Shift.open_shift(request_data["cashRegisterId"], request.user.doctorprofile)
    data = {"cashRegisterId": new_shift["cash_register_id"], "shiftId": new_shift["shift_id"]}
    return JsonResponse({"ok": True, "message": "", "data": data})


@login_required
def close_shift(request):
    result = Shift.close_shift(request.user.doctorprofile)
    return JsonResponse({"ok": result, "message": ""})
