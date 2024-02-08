from api.patients.sql_func import get_patient_control_params, get_patient_control_params_to_hosp
from clients.models import CardControlParam


def get_card_control_param(card_pk, start_date, end_date, code_param_id=None):
    data_params = CardControlParam.get_patient_control_param(card_pk, code_param_id=code_param_id)
    start_date = f"{start_date}-01-01 00:00:00"
    end_date = f"{end_date}-12-31 23:59:59"
    control_params = tuple(data_params.keys())
    if not control_params:
        return None
    paralinic_result = get_patient_control_params(start_date, end_date, control_params, card_pk)
    prev_patient_control_param_id = None
    tmp_result = {"controlParamId": "", "title": "", "purposeValue": {}, "dates": {}}
    step = 0
    result = []
    unique_month = []
    for i in paralinic_result:
        if not i.value:
            continue
        unique_month.append(i.yearmonth_confirm)
        if i.patient_control_param_id != prev_patient_control_param_id:
            if step != 0:
                result.append(tmp_result.copy())
            tmp_result["controlParamId"] = i.patient_control_param_id
            tmp_result["title"] = data_params[i.patient_control_param_id]["title"]
            tmp_result["dates"] = {}
            tmp_result["purposeValue"] = data_params[i.patient_control_param_id]["purpose"]
        if not tmp_result["dates"].get(i.yearmonth_confirm, None):
            tmp_result["dates"][i.yearmonth_confirm] = {}
        tmp_month_date = tmp_result["dates"].get(i.yearmonth_confirm)
        if not tmp_month_date.get(i.confirm, None):
            tmp_month_date[i.confirm] = [{"dir": i.direction, "value": i.value.split()[0]}]
        else:
            tmp_month_date[i.confirm].append({"dir": i.direction, "value": i.value.split()[0]})
        tmp_result["dates"][i.yearmonth_confirm] = tmp_month_date.copy()
        prev_patient_control_param_id = i.patient_control_param_id
        step += 1
    unique_month = sorted(list(set(unique_month)))

    result.append(tmp_result.copy())

    tmp_dates = {i: {} for i in unique_month}
    unique_month_result = [{"title": "Параметр", "purposeValue": "Целевое значение", "dates": tmp_dates}]

    for i in result:
        final_data = tmp_dates.copy()
        for k, v in i['dates'].items():
            final_data[k] = v
        i['dates'] = final_data.copy()
        unique_month_result.append(i)
    return unique_month_result


def get_vital_param_in_hosp(card_pk, parent_iss, code_param_id):
    data_params = CardControlParam.get_patient_control_param(card_pk, code_param_id=code_param_id)
    control_params = tuple(data_params.keys())
    if not control_params:
        return None
    recieve_vital_result = get_patient_control_params_to_hosp(control_params, card_pk, parent_iss)
    if len(recieve_vital_result) > 0:
        return recieve_vital_result[0].value
    else:
        return ""
