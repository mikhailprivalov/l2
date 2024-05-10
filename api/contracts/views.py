from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import simplejson as json
from django.db import transaction

from api.contracts.func import researches_for_billing, get_confirm_data_for_billing, structure_table
from contracts.models import BillingRegister, RawDocumentBillingRegister, PriceName
from directions.models import Issledovaniya
from directory.models import Researches
from laboratory.decorators import group_required
from utils.response import status_response


@login_required
@group_required("Счет: проект")
def create_billing(request):
    body = json.loads(request.body)
    company_id = body.get("companyId")
    hospital_id = body.get("hospitalId")
    date_start = body.get("dateStart")
    date_end = body.get("dateEnd")
    info = body.get("info")
    billing_id = BillingRegister.create_billing(company_id, hospital_id, date_start, date_end, info)
    return JsonResponse({"ok": True, "billingInfo": billing_id})


@login_required
@group_required("Счет: проект")
def update_billing(request):
    body = json.loads(request.body)
    hospital_id = body.get("hospitalId")
    date_start = body.get("dateStart")
    date_end = body.get("dateEnd")
    billing_id = body.get("id")
    info = body.get("info")
    billing_info = BillingRegister.update_billing(billing_id, date_start, date_end, info)
    type_price = body.get("typeCompany")
    data = researches_for_billing(type_price, hospital_id, date_start, date_end)
    structure_data = structure_table(data)
    return JsonResponse({"ok": True, "billingInfo": billing_info, **structure_data})


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
def get_hospital_prices(request):
    body = json.loads(request.body)
    hospital_id = body.get("hospitalId")
    date_start = body.get("dateStart")
    date_end = body.get("dateEnd")
    prices = PriceName.get_hospital_many_prices_by_date(hospital_id, date_start, date_end, is_subcontract=True)
    prices_data = [{"id": i.pk, "label": i.title} for i in prices]
    return JsonResponse({"data": prices_data})



@login_required
@group_required("Счет: проект")
def change_visibility_research(request):
    request_data = json.loads(request.body)
    result = Researches.change_visibility(request_data["researchPk"])
    return status_response(result)


@login_required
@group_required("Счет: проект")
def get_billings(request):
    request_data = json.loads(request.body)
    hospital_id = request_data.get("hospitalId")
    company_id = request_data.get("companyId")
    result = BillingRegister.get_billings(hospital_id, company_id)
    return JsonResponse({"result": result})


@login_required
@group_required("Счет: проект")
def get_billing(request):
    request_data = json.loads(request.body)
    billing_id = request_data.get("billingId")
    result = BillingRegister.get_billing(billing_id)
    type_price = request_data.get("typeCompany")
    data = researches_for_billing(type_price, result["hospitalId"], result["dateStart"], result["dateEnd"])
    structure_data = structure_table(data)
    return JsonResponse({"result": result, **structure_data})
