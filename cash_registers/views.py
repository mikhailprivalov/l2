import uuid
import pytz
from cash_registers.models import CashRegister, Shift, Cheque, ChequeItems
import cash_registers.req as cash_req
import cash_registers.sql_func as sql_func
from directions.models import IstochnikiFinansirovaniya, Napravleniya
from laboratory.settings import TIME_ZONE, PAY_FIN_SOURCE_ID
from laboratory.utils import current_time


def get_cash_registers():
    result = CashRegister.get_cash_registers()
    return result


def open_shift(cash_register_id: int, doctor_profile_id: int):
    result = {"ok": True, "message": ""}
    if cash_register_id:
        shift_job_data = Shift.get_shift_job_data(doctor_profile_id, cash_register_id)
        operator_data, cash_register_data, uuid_data = shift_job_data["operator_data"], shift_job_data["cash_register_data"], shift_job_data["uuid_data"]
        job_body = Shift.create_job_json(cash_register_data, uuid_data, operator_data)
        check_cash_register = cash_req.check_cash_register(cash_register_data, job_open_shift=True)
        if check_cash_register["ok"]:
            job_result = cash_req.send_job(job_body)
            if job_result["ok"]:
                Shift.open_shift(str(uuid_data), cash_register_id, doctor_profile_id)
            else:
                result = job_result
        else:
            result = check_cash_register
    else:
        result = {"ok": False, "message": "Не выбрана касса"}
    return result


def close_shift(cash_register_id: int, doctor_profile_id: int):
    result = {"ok": True, "message": ""}
    if cash_register_id:
        shift_job_data = Shift.get_shift_job_data(doctor_profile_id, cash_register_id)
        operator_data, cash_register_data, uuid_data = shift_job_data["operator_data"], shift_job_data["cash_register_data"], shift_job_data["uuid_data"]
        job_body = Shift.create_job_json(cash_register_data, uuid_data, operator_data, "closeShift")
        check_cash_register = cash_req.check_cash_register(cash_register_data, job_close_shift=True)
        if check_cash_register["ok"]:
            job_result = cash_req.send_job(job_body)
            if job_result["ok"]:
                Shift.close_shift(uuid_data, cash_register_id, doctor_profile_id)
            else:
                result = job_result
        else:
            result = check_cash_register
    else:
        result = {"ok": False, "message": "Не выбрана касса"}
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
            if current_status == "Открывается":
                check_cash_register = cash_req.check_cash_register(cash_register_data, check=True)
            else:
                check_cash_register = cash_req.check_cash_register(cash_register_data, check=True)
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
                result["data"] = data
    return result


def get_service_coasts(directions_ids: list):
    result = {"ok": True, "message": "", "data": {}}
    directions_ids_typle = tuple(directions_ids)
    service_without_coast = False
    summ = 0
    coasts = []
    if not PAY_FIN_SOURCE_ID:
        result = {"ok": False, "message": "Не указан источник финансирования для оплаты", "data": {}}
        return result
    services = sql_func.get_services_by_directions(directions_ids_typle, PAY_FIN_SOURCE_ID)
    if not services:
        result = {"ok": False, "message": "Выбранные направления нельзя оплатить", "data": {}}
        return result
    paid_directions_ids = [service.direction_id for service in services]
    services_ids = tuple([service.id for service in services])
    services_coasts = {}
    for service in services:
        if services_coasts.get(service.id):
            service_coast = services_coasts[service.id]
            count = service_coast["count"] + 1
            service_coast["count"] = count
        else:
            services_coasts[service.id] = {
                "id": service.id,
                "title": service.title,
                "coast": 0,
                "discountRelative": service.def_discount,
                "discountAbsolute": 0,
                "discountedCoast": 0,
                "discountStatic": service.prior_discount,
                "count": 1,
                "total": 0,
            }

    pay_fin_source: IstochnikiFinansirovaniya = IstochnikiFinansirovaniya.objects.filter(pk=PAY_FIN_SOURCE_ID).select_related('contracts').first()
    if pay_fin_source:
        price_id = pay_fin_source.contracts.price_id
        if price_id:
            coasts = sql_func.get_service_coasts(services_ids, price_id)

    for coast in coasts:
        service_coast = coast.coast
        discount_absolute = service_coast * services_coasts[coast.research_id]["discountRelative"]
        discounted_coast = service_coast - discount_absolute
        services_coasts[coast.research_id]["coast"] = service_coast
        services_coasts[coast.research_id]["discountAbsolute"] = discount_absolute
        services_coasts[coast.research_id]["discountedCoast"] = discounted_coast
        total = services_coasts[coast.research_id]["count"] * discounted_coast
        services_coasts[coast.research_id]["total"] = total
        summ += coast.coast

    if len(coasts) < len(services_coasts):
        service_without_coast = True

    service_coasts = [i for i in services_coasts.values()]

    result["data"] = {"coasts": service_coasts, "serviceWithoutCoast": service_without_coast, "paidDirectionsIds": paid_directions_ids}

    return result


def check_count_items(directions_ids, service_coasts):
    """
    Проверка совпадения кол-ва услуг в чеке и кол-ва исследований в направлениях
    """
    total_items_count = 0
    for service in service_coasts:
        total_items_count += int(service["count"])
    total_issledovaniya_count = sql_func.get_total_count_issledovania(directions_ids)
    if total_items_count != total_issledovaniya_count:
        return False
    return True


def payment(shift_id, service_coasts, total_coast, cash, received_cash, electronic, directions_ids):
    result = {"ok": True, "message": "", "cheqId": None}
    result_check_count = check_count_items(directions_ids, service_coasts)
    if not result_check_count:
        result = {"ok": False, "message": "Количество исследований и количество позиций в чеке не совпадает", "cheqId": None}
        return result

    shift = Shift.objects.filter(pk=shift_id).select_related('cash_register').first()
    first_direction: Napravleniya = Napravleniya.objects.filter(pk=directions_ids[0]).first()
    card_id = first_direction.client_id
    cash_register_data = CashRegister.get_meta_data(cash_register_obj=shift.cash_register)
    uuid_data = str(uuid.uuid4())
    type_operations = Cheque.SELL
    items = ChequeItems.create_items(service_coasts)
    payments = Cheque.create_payments(cash, received_cash, electronic)
    total = total_coast
    job_body = Cheque.create_job_json(cash_register_data, uuid_data, type_operations, items, payments, total)
    check_cash_register = cash_req.check_cash_register(cash_register_data)
    if check_cash_register["ok"]:
        job_result = cash_req.send_job(job_body)
        if job_result["ok"]:
            cheq_id = Cheque.create_cheque(shift_id, type_operations, uuid_data, cash, received_cash, electronic, card_id, items)
            result["cheqId"] = cheq_id
        else:
            result = job_result
    else:
        result = check_cash_register

    return result


def get_cheque_data(cheq_id):
    result = {"ok": True, "message": "", "chequeReady": False}
    cheque = Cheque.objects.filter(pk=cheq_id).select_related('shift', 'shift__cash_register').first()
    if not cheque.cancelled:
        cash_register_data = CashRegister.get_meta_data(cash_register_obj=cheque.shift.cash_register)
        uuid_str = str(cheque.uuid)
        check_cash_register = cash_req.check_cash_register(cash_register_data)
        if check_cash_register["ok"]:
            job_result = cash_req.get_job_status(uuid_str, cash_register_data)
            if job_result["ok"]:
                job_status = job_result["data"]["results"][0]
                if job_status["status"] == "ready":
                    time = current_time()
                    cheque.status = True
                    cheque.payment_at = time
                    cheque.row_data["status"] = True
                    cheque.row_data["payment_at"] = time
                    cheque.save()
                    result["chequeReady"] = True
                elif job_status["status"] == "error":
                    cheque.cancelled = True
                    cheque.save()
                    result = {"ok": False, "message": f"Задача заблокирована на кассе: {job_status['error']['description']}"}
            else:
                result = job_result
        else:
            result = check_cash_register

    return result
