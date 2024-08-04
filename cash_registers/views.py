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
    result = {"ok": True, "message": ""}
    shift_job_data = Shift.get_shift_job_data(doctor_profile_id, cash_register_id)
    operator_data, cash_register_data, uuid_data = shift_job_data["operator_data"], shift_job_data["cash_register_data"], shift_job_data["uuid_data"]
    check_cash_register = cash_req.check_cash_register(cash_register_data)
    if check_cash_register["ok"]:
        job_result = cash_req.close_shift(uuid_data, cash_register_data, operator_data)
        if job_result["ok"]:
            Shift.close_shift(uuid_data, cash_register_id, doctor_profile_id)
        else:
            result = job_result
    else:
        result = check_cash_register
    return result


def get_shift_data(doctor_profile_id: int):
    """Проверка смены, открывается, открыта, закрывается, закрыта"""
    data = {"shiftId": None, "cashRegisterId": None, "cashRegisterTitle": "", "status": "Смена закрыта"}
    result = {"ok": True, "data": data}
    shift: Shift = Shift.objects.filter(operator_id=doctor_profile_id, close_status=False).select_related('cash_register').last()
    if shift:
        uuid_data = None
        status = ""
        result["data"] = {"shiftId": shift.pk, "cashRegisterId": shift.cash_register_id, "cashRegisterTitle": shift.cash_register.title, "status": ""}
        if not shift.open_status and shift.open_uuid:
            status = "Смена открывается"
            uuid_data = shift.open_uuid
        elif shift.open_status and not shift.close_uuid:
            status = "Смена открыта"
            result["data"]["status"] = status
        elif shift.open_status and shift.close_uuid:
            status = "Смена закрывается"
            uuid_data = shift.close_uuid

        if uuid_data:
            cash_register_data = CashRegister.get_meta_data(shift.cash_register_id)
            check_cash_register = cash_req.check_cash_register(cash_register_data)
            if check_cash_register["ok"]:
                job_result = cash_req.get_job_status(str(uuid_data), cash_register_data)
                if job_result["ok"]:
                    job_status = job_result["data"]["results"][0]
                    if job_status["status"] == "ready" and status == "Смена открывается":
                        shift.confirm_open_shift()
                        status = "Смена открыта"
                        result["data"]["status"] = status
                    elif job_status["status"] == "ready" and status == "Смена закрывается":
                        shift.confirm_close_shift()
                        status = "Смена закрыта"
                        result["data"]["status"] = status
                else:
                    result = job_result
            else:
                result = check_cash_register

    return result
