from ecp_integration.integration import doctors_has_free_date, get_doctor_ecp_free_slots_by_date
from infomat.sql_func import get_doctors_infomat_has_rmis_location


def get_speciality_infomat(
    speciality_id,
    hosptal_id,
    date_start,
    date_end,
):
    doctors = get_doctors_infomat_has_rmis_location(hosptal_id, speciality_id)
    result = doctors_has_free_date(doctors, date_start, date_end)
    data = [{"rmisLocation": k, "fio": v["fio"], "pk": v["pk"], "tmpDates": v["dates"], "dates": []} for k, v in result["doctors_has_free_date"].items()]
    for r in data:
        for d in r["tmpDates"]:
            free_slots = get_doctor_ecp_free_slots_by_date(r["rmisLocation"], d)
            r["dates"].append({"date": d, "times": free_slots})
    return data
