from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import simplejson as json

from clients.models import CardBase
from contracts.models import BillingRegister
from directions.models import IstochnikiFinansirovaniya
from directory.models import Researches, Unit, LaboratoryMaterial, ResultVariants, MaterialVariants, SubGroupPadrazdeleniye, SubGroupDirectory
from laboratory.decorators import group_required
from podrazdeleniya.models import Podrazdeleniya
from researches.models import Tubes
from statistic.sql_func import statistics_research_by_hospital_for_external_orders
from statistic.views import get_price_company, get_price_hospital
from utils.response import status_response


@login_required
@group_required("Счет: проект")
def get_research_for_billing(request):
    body = json.loads(request.body)
    company_id = body.get("company")
    date_start = "2024-04-01"
    date_end = "2024-04-30"
    hospital_id, sql_result = None, None

    if body.get("typePrice") == "Заказчик":
        hospital_id = company_id
        price = get_price_hospital(hospital_id, date_start, date_end)
        base = CardBase.objects.filter(internal_type=True).first()
        finsource = IstochnikiFinansirovaniya.objects.filter(base=base, title__in=["Договор"], hide=False).first()
        sql_result = statistics_research_by_hospital_for_external_orders(date_start, date_end, hospital_id, finsource.pk)
    result = {}
    for i in sql_result:
        current_data = {
                    "research_id": i.research_id,
                    "research_title": i.research_title,
                    "date_confirm": i.date_confirm,
                    "patient_fio": f"{i.patient_family} {i.patient_name} {i.patient_patronymic}",
                    "patient_born": i.ru_date_born,
                    "tube_number": i.tube_number
                }
        if not result.get(i.patient_card_num):
            result[i.patient_card_num] = [current_data.copy()]
        else:
            result[i.patient_card_num].append(current_data.copy())

    return JsonResponse({"result": result})


@login_required
@group_required("Счет: проект")
def create_new_billing(request):
    body = json.loads(request.body)
    company_id = body.get("companyId")
    hospital_id = body.get("hospitalId")
    billing_id = body.get("billingId")
    date_start = body.get("dateStart")
    date_end = body.get("dateEnd")
    info = body.get("info")
    billing_info = BillingRegister.save_billing(company_id, hospital_id, billing_id, date_start, date_end, info)
    return JsonResponse({"ok": True, "billing_info": billing_info})


@login_required
@group_required("Счет: проект")
def confirm_billing(request):
    body = json.loads(request.body)
    billing_id = body.get("billingId")
    is_confirm_billing = BillingRegister.confirm_billing(billing_id, [])
    return JsonResponse({"ok": is_confirm_billing})


@login_required
@group_required("Счет: проект")
def change_visibility_research(request):
    request_data = json.loads(request.body)
    result = Researches.change_visibility(request_data["researchPk"])
    return status_response(result)


def get_researches_execute_for_company(d_s, d_e, hospital_id, fin_source_pk):
    results = statistics_research_by_hospital_for_external_orders(d_s, d_e, hospital_id, fin_source_pk)
    unique_researches = set([i.research_id for i in results])

    head_data = {i.research_id: i.research.title for i in unique_researches}
    def_value_data = {k: 0 for k in head_data.keys()}
