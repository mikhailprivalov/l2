import datetime
import json

import openpyxl
from dateutil.relativedelta import relativedelta

from statistic import sql_func, structure_sheet


def swab_covid(request_data, response, tr, covid_question_id):
    date_data = request_data.get("date_values")
    date_type = request_data.get("date_type")
    if date_type != "d":
        return ""
    date_values = json.loads(date_data)

    day = date_values.get("date", None)
    if day is None:
        return ""
    day_raw = day.split(".")
    search_date = f"{day_raw[2]}-{day_raw[1]}-{day_raw[0]}"

    d2 = datetime.date(int(day.split(".")[2]), int(day.split(".")[1]), int(day.split(".")[0]))
    d1 = d2 + relativedelta(days=-30)
    d2 = datetime.datetime.combine(d2, datetime.time.max)
    d1 = datetime.datetime.combine(d1, datetime.time.min)
    iss_statistics_covid = sql_func.temp_statistics_covid_call_patient(covid_question_id, d1, d2, "Сдача повторного мазка на COVID", search_date)
    iss_tuple = tuple(set([i.issledovaniye_id for i in iss_statistics_covid]))
    statistics_covid = sql_func.statistics_covid_call_patient(covid_question_id, d1, d2, tuple(["Адрес", "Контактный телефон", "Оператор", "Сдача повторного мазка на COVID"]), iss_tuple)
    wb = openpyxl.Workbook()
    wb.remove(wb.get_sheet_by_name('Sheet'))
    ws = wb.create_sheet('мазок')
    ws = structure_sheet.covid_swab_base(ws)
    data = parse_data(statistics_covid)
    ws = structure_sheet.covid_swab_data(ws, data)
    response['Content-Disposition'] = str.translate("attachment; filename=\"мазки.xlsx\"", tr)
    wb.save(response)
    return response


def parse_data(sql_data):
    people = []
    temp_data = {"Контактный телефон": "", "Оператор": "", "Сдача повторного мазка на COVID": "", "number": "", "fio_patient": "", "Адрес": ""}
    count = 0
    prev_iss_id = None
    for i in sql_data:
        if count != 0 and i.issledovaniye_id != prev_iss_id:
            people.append(temp_data.copy())
            temp_data = {"Контактный телефон": "", "Оператор": "", "Сдача повторного мазка на COVID": "", "number": "", "fio_patient": "", "Адрес": ""}
        temp_data[i.title] = i.value
        temp_data["number"] = i.number
        temp_data["fio_patient"] = i.fio_patient
        prev_iss_id = i.issledovaniye_id
        count += 1
    people.append(temp_data.copy())
    return people
