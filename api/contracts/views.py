from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import simplejson as json
from django.db import transaction

from api.contracts.func import researches_for_billing, get_confirm_data_for_billing, structure_table
from contracts.models import BillingRegister, RawDocumentBillingRegister
from directions.models import Issledovaniya
from directory.models import Researches
from laboratory.decorators import group_required
from statistic.sql_func import statistics_research_by_hospital_for_external_orders
from utils.response import status_response


@login_required
@group_required("Счет: проект")
def get_research_for_billing(request):
    body = json.loads(request.body)
    company_id = body.get("company")
    date_start = "2024-04-01"
    date_end = "2024-04-30"
    type_price = body.get("typePrice")
    data = researches_for_billing(type_price, company_id, date_start, date_end)
    structure_data = structure_table(data)
    return JsonResponse(data)


@login_required
@group_required("Счет: проект")
def create_billing(request):
    body = json.loads(request.body)
    company_id = body.get("companyId")
    hospital_id = body.get("hospitalId")
    date_start = body.get("dateStart")
    date_end = body.get("dateEnd")
    info = body.get("info")
    billing_info = BillingRegister.create_billing(company_id, hospital_id, date_start, date_end, info)
    type_price = body.get("typeCompany")
    data = researches_for_billing(type_price, hospital_id, date_start, date_end)
    structure_data = structure_table(data)
    return JsonResponse({"ok": True, "billing_info": billing_info, **structure_data })


@login_required
@group_required("Счет: проект")
def update_billing(request):
    body = json.loads(request.body)
    hospital_id = body.get("hospitalId")
    date_start = body.get("dateStart")
    date_end = body.get("dateEnd")
    billing_id = body.get("billingId")
    info = body.get("info")
    billing_info = BillingRegister.update_billing(billing_id, date_start, date_end, info)
    type_price = body.get("typeCompany")
    data = researches_for_billing(type_price, hospital_id, date_start, date_end)
    structure_data = structure_table(data)
    return JsonResponse({"ok": True, "billingId": billing_info, **structure_data})


@login_required
@group_required("Счет: проект")
def confirm_billing(request):
    body = json.loads(request.body)
    billing_id = body.get("billingId")
    iss_ids = body.get("issIds")
    price_id = body.get("priceId")
    with transaction.atomic():
        is_confirm_billing = BillingRegister.confirm_billing(billing_id)
        set_billing_id_for_iss = Issledovaniya.save_billing(billing_id, iss_ids)
        data_confirm_billing = get_confirm_data_for_billing(price_id, billing_id)
        raw_document_pk = RawDocumentBillingRegister.create_raw_billing_data(billing_id, data_confirm_billing)

    return JsonResponse({"ok": is_confirm_billing and set_billing_id_for_iss and raw_document_pk})


@login_required
@group_required("Счет: проект")
def get_data_for_confirmed_billing(request):
    body = json.loads(request.body)
    billing_id = body.get("billingId")
    return JsonResponse({"ok": True})


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


@login_required
@group_required("Счет: проект")
def get_billings(request):
    request_data = json.loads(request.body)
    hospital_id = request_data.get('hospitalId')
    company_id = request_data.get('companyId')
    result = BillingRegister.get_billings(hospital_id, company_id)
    return JsonResponse({"result": result})


@login_required
@group_required("Счет: проект")
def get_billing(request):
    request_data = json.loads(request.body)
    billing_id = request_data.get('billingId')
    result = BillingRegister.get_billing(billing_id)
    return JsonResponse({"result": result})
