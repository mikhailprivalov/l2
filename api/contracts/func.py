from clients.models import CardBase
from contracts.models import BillingRegister
from contracts.sql_func import get_research_coast_by_prce, get_data_for_conform_billing
from directions.models import IstochnikiFinansirovaniya
from statistic.sql_func import statistics_research_by_hospital_for_external_orders
from statistic.views import get_price_hospital


def researches_for_billing(type_price, company_id, date_start, date_end):
    sql_result = None
    research_coast = {}
    price = None
    if type_price == "Заказчик":
        hospital_id = company_id
        price = get_price_hospital(hospital_id, date_start, date_end)
        base = CardBase.objects.filter(internal_type=True).first()
        finsource = IstochnikiFinansirovaniya.objects.filter(base=base, title__in=["Договор"], hide=False).first()
        sql_result = statistics_research_by_hospital_for_external_orders(date_start, date_end, hospital_id, finsource.pk)
        coast_research_price = get_research_coast_by_prce((price.pk,))
        research_coast = {coast.research_id: float(coast.coast) for coast in coast_research_price}
    result = {}
    iss_data = set()
    if sql_result:
        for i in sql_result:
            iss_data.add(i.iss_id)
            current_data = {
                "research_id": i.research_id,
                "research_title": i.research_title,
                "date_confirm": i.date_confirm,
                "patient_fio": f"{i.patient_family} {i.patient_name} {i.patient_patronymic}",
                "patient_born": i.ru_date_born,
                "tube_number": i.tube_number,
                "coast": research_coast.get(i.research_id, 0),
                "code_nmu": i.code_nmu,
                "internal_code": i.internal_code
            }
            if not result.get(i.patient_card_num):
                result[i.patient_card_num] = [current_data.copy()]
            else:
                result[i.patient_card_num].append(current_data.copy())
    return {"result": result, "issIds": list(iss_data), "priceId": price.pk}


def get_confirm_data_for_billing(price_id, billing_id):
    sql_result = get_data_for_conform_billing(billing_id)
    coast_research_price = get_research_coast_by_prce((price_id,))
    research_coast = {coast.research_id: float(coast.coast) for coast in coast_research_price}
    result = {}
    iss_data = set()
    for i in sql_result:
        iss_data.add(i.iss_id)
        current_data = {
            "research_id": i.research_id,
            "research_title": i.research_title,
            "date_confirm": i.date_confirm,
            "patient_fio": f"{i.patient_family} {i.patient_name} {i.patient_patronymic}",
            "patient_born": i.ru_date_born,
            "tube_number": i.tube_number,
            "coast": research_coast.get(i.research_id, 0)
        }
        if not result.get(i.patient_card_num):
            result[i.patient_card_num] = [current_data.copy()]
        else:
            result[i.patient_card_num].append(current_data.copy())
    billing_register_data = BillingRegister.objects.filter(id=billing_id).first()
    company_title = billing_register_data.company.title if billing_register_data.company else ""
    hospital_title = billing_register_data.hospital.title if billing_register_data.hospital else ""
    organization = {
        "company": company_title,
        "hospital": hospital_title,
        "create_at": billing_register_data.create_at,
        "who_create": billing_register_data.who_create.get_fio(),
        "date_start": billing_register_data.date_start,
        "date_end": billing_register_data.date_end,
        "info": billing_register_data.info,
        "is_confirmed": billing_register_data.is_confirmed,
    }
    return {"result": result, "issIds": list(iss_data), "organization": organization}


def structure_table(data_researches):
    columns = [
        {"key": "serialNumber", "field": "serialNumber", "title": "№", "align": "left", "width": 150, "fixed": 'left'},
        {"key": "patientFio", "field": "patientFio", "title": "Пациент", "align": "left", "width": 150, "fixed": 'left'},
        {"key": "patientBirthDay", "field": "patientBirthDay", "title": "Дата рожд.", "align": "left", "width": 150, "fixed": 'left'},
        {"key": "executeDate", "field": "executeDate", "title": "Дата вып.", "align": "left", "width": 150, "fixed": 'left'},
        {"key": "internalId", "field": "internalId", "title": "Код", "align": "left", "width": 150, "fixed": 'left'},
        {"key": "codeNMU", "field": "codeNMU", "title": "Код НМУ", "align": "left", "width": 150, "fixed": 'left'},
        {"key": "researchTitle", "field": "researchTitle", "title": "Наименование услуги", "align": "left", "width": 150, "fixed": 'left'},
        {"key": "tubeNumber", "field": "tubeNumber", "title": "Лаб. номер", "align": "left", "width": 150, "fixed": 'left'},
        {"key": "count", "field": "count", "title": "Кол.", "align": "left", "width": 150, "fixed": 'left'},
        {"key": "coast", "field": "coast", "title": "Цена", "align": "left", "width": 150, "fixed": 'left'},
        {"key": "summ", "field": "coast", "title": "Стоимость, руб", "align": "left", "width": 150, "fixed": 'left'},
    ]
    step = 0
    for card_id, research_data in data_researches.get("result").items():
        step += 1
        patient_data = {}
        for i in research_data:
            if not patient_data.get(card_id):
                patient_data[card_id] = {"serialNumber": step, "patientFio": i.get("patient_fio"), "patientBirthDay": i.get("patient_born"), "tubeNumber": i.get("tube_number"),
                                         "coast": i.get("coast"), "researchTitle": i.get("research_title"), "internalId": i.get("internal_code"), "codeNMU": i.get("code_nmu")}
            else:
                patient_data[f"{card_id} {i.get('research_id')}"] = {"serialNumber": "", "patientFio": "", "patientBirthDay": "", "tubeNumber": i.get("tube_number"),
                                         "coast": i.get("coast"), "researchTitle": i.get("research_title"), "internalId": i.get("internal_code"),"codeNMU": i.get("code_nmu")}

    table_data = [v for v in patient_data.values()]
    return {"columns": columns, "table_data": table_data}
