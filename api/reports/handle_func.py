def patologistology_buh(data):
    prev_direction = None
    step = 0
    result = []
    tmp_dict_data = {
        "hospital": "",
        "direction": "",
        "fio_patient": "",
        "born_patient": "",
        "polis": "",
        "snils": "",
        "visit_date": "",
        "mcb10_code": "",
        "fin_source": "",
        "price_category": "",
        "purpose": "",
        "service_code": "",
    }
    match_keys = {
        "Полис ОМС": "polis",
        "СНИЛС": "snils",
        "ФИО пациента": "fio_patient",
        "Дата рождения": "born_patient",
        "Дата регистрации": "visit_date",
        "Медицинские услуги": "service_code",
        "Код по МКБ": "mcb10_code",
    }
    tmp_data = tmp_dict_data.copy()

    for i in data:
        if prev_direction != i.direction_id and step != 0:
            result.append(tmp_data.copy())
            tmp_data = tmp_dict_data.copy()
        tmp_data["direction"] = i.direction_id
        tmp_data["fin_source"] = i.iss_finsource_title
        tmp_data["price_category"] = i.iss_price_category
        tmp_data["hospital"] = i.hosp_title
        prev_direction = i.direction_id
        step += 1
        if not match_keys.get(i.field_title, None):
            continue
        else:
            val = match_keys.get(i.field_title)
            tmp_data[val] = i.value

    result.append(tmp_data.copy())
    return result
