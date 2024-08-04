from cash_registers.models import CashRegister, Shift
import cash_registers.req as cash_req


def get_cash_registers():
    result = CashRegister.get_cash_registers()
    return result


def open_shift(cash_register_id: int, doctor_profile_id: int):
    result = {"ok": True, "message": ""}
    shift_job_data = Shift.get_shift_job_data(doctor_profile_id, cash_register_id)
    operator_data, cash_register_data, uuid_data = shift_job_data["operator_data"], shift_job_data["cash_register_data"], shift_job_data["uuid_data"]
    check_cash_register = cash_req.check_cash_register(cash_register_data)
    if check_cash_register["ok"]:
        job_result = cash_req.open_shift(uuid_data, cash_register_data, operator_data)
        if job_result["ok"]:
            Shift.open_shift(str(uuid_data), cash_register_id, doctor_profile_id)
        else:
            result = job_result
    else:
        result = check_cash_register
    return result


def close_shift(cash_register_id: int, doctor_profile_id: int):
    shift_job_data = Shift.get_shift_job_data(doctor_profile_id, cash_register_id)
    operator_data, cash_register_data, uuid_data = shift_job_data["operator_data"], shift_job_data["cash_register_data"], shift_job_data["uuid_data"]
    check_cash_register = cash_req.check_cash_register(cash_register_data)
    if not check_cash_register["ok"]:
        return check_cash_register
    job_result = cash_req.close_shift(uuid_data, cash_register_data, operator_data)
    if not job_result["ok"]:
        return job_result
    result = Shift.close_shift(uuid_data, cash_register_id, doctor_profile_id)
    return {"ok": result, "message": ""}


def get_shift_data(doctor_profile_id: int):
    """Проверка смены, status 0 - смена открывается, 1 - смена открыта, 2 - смена закрывается, -1 - Смена закрыта,"""
    shift: Shift = Shift.objects.filter(operator_id=doctor_profile_id, close_status=False).select_related('cash_register').last()
    uuid_data = None
    status = None
    if not shift:
        data = {"shiftId": None, "cashRegisterId": None, "cashRegisterTitle": "", "status": -1}
        return {"ok": True, "data": data}
    if not shift.open_status and shift.open_uuid:
        status = 0
        uuid_data = shift.open_uuid
    elif shift.open_status and not shift.close_uuid:
        status = 1
    elif shift.open_status and shift.close_uuid:
        status = 2
        uuid_data = shift.close_uuid
    if not uuid_data:
        data = {"shiftId": shift.pk, "cashRegisterId": shift.cash_register_id, "cashRegisterTitle": shift.cash_register.title, "status": status}
        return {"ok": True, "data": data}

    cash_register_data = CashRegister.get_meta_data(shift.cash_register_id)
    check_cash_register = cash_req.check_cash_register(cash_register_data)
    if not check_cash_register["ok"]:
        return check_cash_register
    job_result = cash_req.get_job_status(str(uuid_data), cash_register_data)
    if not job_result["ok"]:
        return {"ok": False, "message": "Ошибка проверки задания"}
    job_status = job_result["data"]["results"][0]
    if job_status["status"] == "ready" and status == 0:
        shift.confirm_open_shift()
        status = 1
    elif job_status["status"] == "ready" and status == 2:
        shift.confirm_close_shift()
        status = -1
    data = {"shiftId": shift.pk, "cashRegisterId": shift.cash_register_id, "cashRegisterTitle": shift.cash_register.title, "status": status}
    return {"ok": True, "data": data}
