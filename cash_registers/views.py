import uuid

from cash_registers.models import CashRegister, Shift
import cash_registers.atol as atol
from users.models import DoctorProfile


def get_cash_registers():
    result = CashRegister.get_cash_registers()
    return result


def get_cash_register_data(cash_register_id: int):
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
    if not job_result["ok"]:
        return job_result
    new_shift = Shift.open_shift(uuid_data, cash_register_id, doctor_profile_id)
    data = {"cashRegisterId": new_shift["cash_register_id"], "shiftId": new_shift["shift_id"]}
    return {"ok": True, "message": "", "data": data}


def close_shift(cash_register_id: int, doctor_profile_id: int):
    operator_data, cash_register_data, uuid_data = get_shift_job_data(doctor_profile_id, cash_register_id)
    job_result = atol.close_shift(uuid_data, cash_register_data, operator_data)
    if not job_result["ok"]:
        return job_result
    result = Shift.close_shift(uuid_data, cash_register_id, doctor_profile_id)
    return {"ok": result, "message": ""}


def get_shift_data(doctor_profile_id: int):
    shift_data = Shift.get_shift_data(doctor_profile_id)
    status = None
    if not shift_data:
        return {"ok": False, "data": shift_data}
    if not shift_data["uuid"]:
        data = {"shiftId": shift_data["shift_id"], "cashRegisterId": shift_data["cash_register_id"], "cashRegisterTitle": shift_data["cash_register_title"], "status": shift_data["status"]}
        return {"ok": True, "data": data}
    cash_register_data = get_cash_register_data(shift_data["cash_register_id"])
    job_result = atol.get_job_status(shift_data["uuid"], cash_register_data)
    if not job_result["ok"]:
        return {"ok": False, "message": "Не удалось запросить статус"}
    if shift_data["status"] == 0:
        confirm_open = Shift.confirm_open_shift(shift_data["shift_id"])
        status = 1
    else:
        confirm_close = Shift.confirm_close_shift(shift_data["shift_id"])
        return {"ok": False, "data": None}
    data = {"shiftId": shift_data["shift_id"], "cashRegisterId": shift_data["cash_register_id"], "cashRegisterTitle": shift_data["cash_register_title"], "status": status}
    return {"ok": True, "data": data}
