import pytz

from cash_registers.models import CashRegister, Shift
import cash_registers.req as cash_req
import cash_registers.sql_func as sql_func
from laboratory.settings import TIME_ZONE


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
    """Проверка статуса смены: открывается, открыта, закрывается, закрыта"""
    data = {"shiftId": None, "cashRegisterId": None, "cashRegisterTitle": "", "open_at": None, "status": "Закрыта"}
    result = {"ok": True, "message": "", "data": data}
    shift: Shift = Shift.objects.filter(operator_id=doctor_profile_id, close_status=False).select_related('cash_register').last()
    if shift:
        shift_status = shift.get_shift_status()
        current_status = shift_status["status"]
        uuid_data = shift_status["uuid"]
        open_at = ""
        if shift.open_at:
            open_at = shift.open_at.astimezone(pytz.timezone(TIME_ZONE)).strftime('%d.%m.%Y %H:%M')
        result["data"] = {"shiftId": shift.pk, "cashRegisterId": shift.cash_register_id, "cashRegisterTitle": shift.cash_register.title, "open_at": open_at, "status": current_status}

        if uuid_data:
            cash_register_data = CashRegister.get_meta_data(cash_register_obj=shift.cash_register)
            check_cash_register = cash_req.check_cash_register(cash_register_data)
            if check_cash_register["ok"]:
                job_result = cash_req.get_job_status(str(uuid_data), cash_register_data)
                if job_result["ok"]:
                    job_status = job_result["data"]["results"][0]
                    if job_status["status"] == "ready":
                        result["data"]["status"] = Shift.change_status(current_status, job_status, shift)
                        open_at = shift.open_at.astimezone(pytz.timezone(TIME_ZONE)).strftime('%d.%m.%Y %H:%M')
                        result["data"]["open_at"] = open_at
                    elif job_status["status"] == "error":
                        result = {"ok": False, "message": "Задача заблокирована на кассе"}
                else:
                    result = job_result
            else:
                result = check_cash_register
    return result


def get_service_coasts(service_ids: list):
    if not service_ids:
        return
    service_ids_tuple = tuple(service_ids)
    service_without_coast = False
    summ = 0
    services = sql_func.get_services(service_ids_tuple)
    services_coast = {service.id: {"id": service.id, "title": service.title, "coast": 0} for service in services}
    coasts = sql_func.get_service_coasts(service_ids_tuple)

    for coast in coasts:
        services_coast[coast.research_id]["coast"] = coast.coast
        summ += coast.coast

    if len(coasts) < len(service_ids):
        service_without_coast = True

    result = {"coasts": [i for i in services_coast.values()], "summ": summ, "serviceWithoutCoast": service_without_coast}

    return result


def payment(shift_id, coasts, summ_coasts, discount, cash, received_cash, card, for_pay, card_id):
    result = {"ok": True, "message": "", "cheqId": None}
    shift = Shift.objects.filter(pk=shift_id).select_related('cash_register').first()
    cash_register_data = CashRegister.get_meta_data(cash_register_obj=shift.cash_register)
    print(cash_register_data)

    return result
