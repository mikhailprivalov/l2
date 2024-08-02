import uuid

from cash_registers.models import CashRegister, Shift
import cash_registers.atol as atol
from users.models import DoctorProfile


def get_cash_registers():
    result = CashRegister.get_cash_registers()
    return result


def get_cash_register_data(cash_register_id):
    cash_register: CashRegister = CashRegister.objects.get(pk=cash_register_id)
    cash_register_data = {"address": cash_register.ip_address, "port": cash_register.port, "login": cash_register.login, "password": cash_register.password}
    return cash_register_data


def get_shift_job_data(doctor_profile_id: int, cash_register_id):
    operator: DoctorProfile = DoctorProfile.objects.get(pk=doctor_profile_id)
    operator_data = {"name": operator.get_full_fio(), "vatin": operator.inn}
    cash_register_data = get_cash_register_data(cash_register_id)
    uuid_data = str(uuid.uuid4())
    return operator_data, cash_register_data, uuid_data


def open_shift(cash_register_id: int, doctor_profile_id: int):
    check_shift = Shift.check_shift(cash_register_id, doctor_profile_id)
    if not check_shift["ok"]:
        return check_shift
    operator_data, cash_register_data, uuid_data = get_shift_job_data(doctor_profile_id, cash_register_id)
    job_result = atol.open_shift(uuid_data, cash_register_data, operator_data)
    print(job_result)
    if job_result.get("error"):
        print('Произошла ошибка на этапе подключения к cash')
    # if not job_result["ok"]:
    #     return job_result
    # new_shift = Shift.open_shift(str(uuid_data), cash_register_id, doctor_profile_id)
    # data = {"cashRegisterId": new_shift["cash_register_id"], "shiftId": new_shift["shift_id"]}
    return {"ok": False, "message": "", "data": {}}


def close_shift(cash_register_id: int, doctor_profile_id: int):
    operator_data, cash_register_data, uuid_data = get_shift_job_data(doctor_profile_id, cash_register_id)
    # job_result = atol.close_shift(str(uuid_data), cash_register_data, operator_data)
    # if not job_result["ok"]:
    #     return job_result
    result = Shift.close_shift(uuid_data, cash_register_id, doctor_profile_id)
    return {"ok": result, "message": ""}


def get_shift_data(doctor_profile_id: int):
    shift: Shift = Shift.objects.filter(operator_id=doctor_profile_id, close_status=False).select_related('cash_register').last()
    uuid_data = None
    status = None
    if not shift:
        return {"ok": False, "data": shift}
    if not shift.open_status and shift.open_uuid:
        status = 0
        uuid_data = shift.open_uuid
    elif shift.open_status and not shift.close_uuid:
        status = 1
    elif shift.open_status and shift.close_uuid:
        status = 2
        uuid_data = shift.close_uuid
    cash_register_data = get_cash_register_data(shift.cash_register_id)
    # job_result = atol.get_job_status(uuid_data, cash_register_data)
    # print(job_result)
    # if status == 0:
    #     confirm_open = Shift.confirm_open_shift(shift.pk)
    #     status = 1
    # elif status == 2:
    #     confirm_close = Shift.confirm_close_shift(shift.pk)

    data = {"shiftId": shift.pk, "cashRegisterId": shift.cash_register_id, "cashRegisterTitle": shift.cash_register.title, "status": status}
    return {"ok": True, "data": data}
