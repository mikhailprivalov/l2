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
                "coast": research_coast.get(i.research_id, 0)
            }
            if not result.get(i.patient_card_num):
                result[i.patient_card_num] = [current_data.copy()]
            else:
                result[i.patient_card_num].append(current_data.copy())
    return {"result": result, "issIds": list(iss_data), "priceIk": price.pk}


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
