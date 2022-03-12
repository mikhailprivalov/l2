from copy import deepcopy
from directions.models import Issledovaniya


def death_form_result_parse(data, reserved=False):
    tmp_data = {}
    data_return = []
    count = 0
    prev_issledovaniye_id = None
    direction = ""
    for i in data:
        if i.issledovaniye_id != prev_issledovaniye_id and count > 0:
            if not tmp_data.get("Заполнил", None):
                iss = Issledovaniya.objects.filter(pk=prev_issledovaniye_id).first()
                if iss and iss.doc_confirmation:
                    tmp_data["Заполнил"] = iss.doc_confirmation.get_full_fio()
            tmp_data["napravleniye_id"] = direction
            tmp_data["issledovaniye_id"] = prev_issledovaniye_id
            data_return.append(deepcopy(tmp_data))
            tmp_data = {}
        if not reserved and i.json_value:
            tmp_data[i.title] = i.json_value
        else:
            tmp_data[i.title] = i.value
        tmp_data["fio_patient"] = i.fio_patient
        tmp_data["sex"] = i.sex
        tmp_data["hosp_title"] = i.hosp_title or ""
        if i.hosp_okpo:
            tmp_data["hosp_okpo"] = i.hosp_okpo
        else:
            tmp_data["hosp_okpo"] = ""
        if i.hosp_okato:
            tmp_data["hosp_okato"] = i.hosp_okato
        else:
            tmp_data["hosp_okato"] = ""
        if reserved:
            tmp_data["date_create"] = i.date_create or ""
            tmp_data["napravleniye_id"] = i.napravleniye_id or ""
        prev_issledovaniye_id = i.issledovaniye_id
        count += 1
        direction = i.napravleniye_id or ""

    if not tmp_data.get("Заполнил", None):
        iss: Issledovaniya = Issledovaniya.objects.filter(pk=prev_issledovaniye_id).first()
        if iss and iss.doc_confirmation:
            tmp_data["Заполнил"] = iss.doc_confirmation.get_full_fio()

    tmp_data["napravleniye_id"] = direction
    tmp_data["issledovaniye_id"] = prev_issledovaniye_id
    data_return.append(deepcopy(tmp_data))

    return data_return


def get_unique_directions(data):
    data_issledovaniye_id = tuple(set([i.issledovaniye_id or "" for i in data]))
    return data_issledovaniye_id


def weapon_form_result_parse(data, reserved=False):
    tmp_data = {}
    data_return = []
    count = 0
    prev_issledovaniye_id = None
    direction = ""
    for i in data:
        if i.issledovaniye_id != prev_issledovaniye_id and count > 0:
            if not tmp_data.get("Врач", None):
                iss = Issledovaniya.objects.filter(pk=prev_issledovaniye_id).first()
                if iss and iss.doc_confirmation:
                    tmp_data["Врач"] = iss.doc_confirmation.get_full_fio()
            tmp_data["napravleniye_id"] = direction
            tmp_data["issledovaniye_id"] = prev_issledovaniye_id
            data_return.append(deepcopy(tmp_data))
            tmp_data = {}
        if not reserved and i.json_value:
            tmp_data[i.title] = i.json_value["address"]
        else:
            tmp_data[i.title] = i.value

        tmp_data["fio_patient"] = i.fio_patient
        tmp_data["hosp_title"] = i.hosp_title or ""
        prev_issledovaniye_id = i.issledovaniye_id
        count += 1
        direction = i.napravleniye_id or ""

    if not tmp_data.get("Врач", None):
        iss: Issledovaniya = Issledovaniya.objects.filter(pk=prev_issledovaniye_id).first()
        if iss and iss.doc_confirmation:
            tmp_data["Врач"] = iss.doc_confirmation.get_full_fio()

    tmp_data["napravleniye_id"] = direction
    tmp_data["issledovaniye_id"] = prev_issledovaniye_id
    data_return.append(deepcopy(tmp_data))

    return data_return




