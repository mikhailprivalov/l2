from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import simplejson as json
from django.db import transaction

from api.contracts.func import researches_for_billing, get_confirm_data_for_billing, structure_table
from contracts.models import BillingRegister, RawDocumentBillingRegister, PriceName
from directions.models import Issledovaniya
from directory.models import Researches
from laboratory.decorators import group_required
from slog.models import Log
from users.models import DoctorProfile
from utils.response import status_response


@login_required
@group_required("Счет: проект")
def create_billing(request):
    body = json.loads(request.body)
    company_id = body.get("companyId")
    hospital_id = body.get("hospitalId")
    date_start = body.get("dateStart")
    date_end = body.get("dateEnd")
    price_id = body.get("priceId")
    info = body.get("info")
    date_from = body.get("dateFrom")
    registry_number = body.get("registryNumber")
    billing_id = BillingRegister.create_billing(company_id, hospital_id, date_start, date_end, info, price_id, date_from, registry_number)
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
    price_id = body.get("priceId")
    date_from = body.get("dateFrom")
    registry_number = body.get("registryNumber")
    billing_data = BillingRegister.objects.filter(pk=billing_id).first()
    if not billing_data.is_confirmed:
        billing_info = BillingRegister.update_billing(billing_id, date_start, date_end, info, price_id, date_from, registry_number)
        type_price = body.get("typeCompany")
        data = researches_for_billing(type_price, hospital_id, date_start, date_end, price_id, billing_data.is_confirmed, billing_id)
        structure_data = structure_table(data)
        return JsonResponse({"ok": True, "billingInfo": billing_info, **structure_data})


@login_required
@group_required("Счет: проект")
def confirm_billing(request):
    body = json.loads(request.body)
    billing_id = body.get("id")
    type_price = body.get("typeCompany")
    billing_data = BillingRegister.objects.filter(pk=billing_id).first()
    if not billing_data.is_confirmed:
        hospital_id = billing_data.hospital_id
        date_start = billing_data.date_start
        date_end = billing_data.date_end
        price_id = billing_data.price_id

        data = researches_for_billing(type_price, hospital_id, date_start, date_end, price_id, billing_data.is_confirmed, billing_id)
        iss_ids = data["issIds"]
        user_who_create = request.user.doctorprofile

        with transaction.atomic():
            is_confirm_billing = BillingRegister.confirm_billing(billing_id, user_who_create)
            set_billing_id_for_iss = Issledovaniya.save_billing(billing_id, iss_ids)
            data_confirm_billing = get_confirm_data_for_billing(price_id, billing_id)
            raw_document_pk = RawDocumentBillingRegister.create_raw_billing_data(billing_id, data_confirm_billing)
            Log.log(
                billing_data.pk,
                200000,
                request.user.doctorprofile,
                {
                    "billing": {"pk": billing_data.pk, "date_from": str(billing_data.date_from), "registry_number": billing_data.registry_number},
                    "who_confirm": {"pk": user_who_create.pk, "family": user_who_create.family, "name": user_who_create.name, "patronymic": user_who_create.patronymic},
                },
            )
        structure_data = structure_table(data)
        return JsonResponse({"ok": is_confirm_billing and set_billing_id_for_iss and raw_document_pk, **structure_data})


@login_required
@group_required("Счет: проект")
def cancel_billing(request):
    body = json.loads(request.body)
    billing_id = body.get("id")
    billing_data = BillingRegister.objects.filter(pk=billing_id).first()
    if billing_data.is_confirmed:
        user_who_create: DoctorProfile = request.user.doctorprofile
        with transaction.atomic():
            billing_data.is_confirmed = False
            billing_data.who_create = user_who_create
            billing_data.save()
            Issledovaniya.cancel_billing(billing_id)
            Log.log(
                billing_data.pk,
                200001,
                request.user.doctorprofile,
                {
                    "billing": {"pk": billing_data.pk, "date_from": str(billing_data.date_from), "registry_number": billing_data.registry_number},
                    "who_cancel": {"pk": user_who_create.pk, "family": user_who_create.family, "name": user_who_create.name, "patronymic": user_who_create.patronymic}
                 },
            )
            return JsonResponse({"ok": True})


@login_required
@group_required("Счет: проект")
def get_hospital_prices(request):
    body = json.loads(request.body)
    hospital_id = body.get("hospitalId")
    date_start = body.get("dateStart")
    date_end = body.get("dateEnd")
    if not (date_start) or not (date_end):
        prices_data = []
    else:
        prices = PriceName.get_hospital_many_prices_by_date(hospital_id, date_start, date_end, is_subcontract=True)
        prices_data = [{"id": i.pk, "label": i.title, "contractNumber": i.contract_number} for i in prices]
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
    data = researches_for_billing(type_price, result["hospitalId"], result["dateStart"], result["dateEnd"], result["priceId"], result["isConfirmed"], billing_id)
    if not data["ok"]:
        return JsonResponse({"ok": data["ok"], "result": [], "message": data["message"]})
    structure_data = structure_table(data)
    return JsonResponse({"ok": True, "result": result, "message": "", **structure_data})
