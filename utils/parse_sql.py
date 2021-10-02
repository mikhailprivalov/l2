from copy import deepcopy


def death_form_result_parse(data, reserved=False):
    tmp_data = {}
    data_return = []
    count = 0
    prev_issledovaniye_id = None
    for i in data:
        if i.issledovaniye_id != prev_issledovaniye_id and count > 0:
            data_return.append(deepcopy(tmp_data))
            tmp_data = {}
        if not reserved and i.json_value:
            tmp_data[i.title] = i.json_value
        else:
            tmp_data[i.title] = i.value
        tmp_data["fio_patient"] = i.fio_patient
        tmp_data["sex"] = i.sex
        tmp_data["hosp_title"] = i.hosp_title
        if reserved:
            tmp_data["napravleniye_id"] = i.napravleniye_id or ""
            tmp_data["date_create"] = i.date_create or ""
        prev_issledovaniye_id = i.issledovaniye_id
        count += 1
    data_return.append(deepcopy(tmp_data))
    return data_return
