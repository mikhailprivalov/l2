import directions.models as directions
from contracts.models import Company, PriceName
from hospitals.models import Hospitals
from django.test import Client as TC
import simplejson as json
import base64


def check_correct_hosp(request, oid_org):
    if not oid_org:
        return {"OK": False, "message": 'Должно быть указано org.oid'}

    hospital = Hospitals.objects.filter(oid=oid_org).first()
    if not hospital:
        return {"OK": False, "message": 'Организация не найдена'}

    if not request.user.hospitals.filter(pk=hospital.pk).exists():
        return {"OK": False, "message": 'Нет доступа в переданную организацию'}

    return {"OK": True, "hospital": hospital}


def check_correct_hospital_company(request, ogrn):
    if not ogrn:
        return {"OK": False, "message": 'Должно быть указано ОГРН'}

    hospital = Hospitals.objects.filter(ogrn=ogrn).first()
    company = Company.objects.filter(ogrn=ogrn).first()
    is_company = False
    if company:
        is_company = True
    if not hospital and not company:
        return {"OK": False, "message": 'Организация не найдена'}
    if not is_company:
        if not request.user.hospitals.filter(pk=hospital.pk).exists():
            return {"OK": False, "message": 'Нет доступа в переданную организацию'}
    else:
        if not request.user.companies.filter(pk=company.pk).exists():
            return {"OK": False, "message": 'Нет доступа в переданную компанию'}

    return {"OK": True, "hospital": hospital, "company": company, "is_company": is_company}


def check_correct_hospital_company_for_price(request, price_code, price_id):
    price = PriceName.get_price_by_id_symbol_code(price_code, price_id)
    if not price:
        return {"OK": False, "message": 'Нет прайса'}
    if price and price.hospital:
        if not request.user.hospitals.filter(pk=price.hospital.pk).exists():
            return {"OK": False, "message": 'Нет доступа в переданную организацию'}
    if price and price.company:
        if not request.user.companies.filter(pk=price.company.pk).exists():
            return {"OK": False, "message": 'Нет доступа в переданную компанию'}

    return {"OK": True, "price": price}


def get_data_direction_with_param(direction_num):
    direction: directions.Napravleniya = directions.Napravleniya.objects.select_related('istochnik_f', 'client', 'client__individual', 'client__base').get(pk=direction_num)
    card = direction.client
    individual = card.individual
    iss = directions.Issledovaniya.objects.filter(
        napravleniye=direction,
    ).select_related('research')

    if not iss:
        return False

    services = [{"title": i.research.title, "code": i.research.code} for i in iss]

    direction_params_obj = directions.DirectionParamsResult.objects.filter(napravleniye_id=direction_num)
    direction_params = {dp.title: dp.value for dp in direction_params_obj}
    return {
        "pk": direction_num,
        "hosp": direction.hospital.title,
        "createdAt": direction.data_sozdaniya,
        "patient": {
            **card.get_data_individual(full_empty=True, only_json_serializable=True),
            "family": individual.family,
            "name": individual.name,
            "patronymic": individual.patronymic,
            "birthday": individual.birthday,
            "docs": card.get_n3_documents(),
            "sex": individual.sex,
        },
        "finSourceTitle": direction.istochnik_f.title if direction.istochnik_f else '',
        "priceCategory": direction.price_category.title if direction.price_category else '',
        "services": services,
        "directionParams": direction_params,
    }


def direction_pdf_result(pk):
    result = direction_pdf_content(pk)
    pdf_content = base64.b64encode(result).decode('utf-8')
    return pdf_content


def direction_pdf_content(direction_id):
    localclient = TC(enforce_csrf_checks=False)
    addr = "/results/pdf"
    params = {"pk": json.dumps([direction_id]), 'leftnone': '1', 'token': "8d63a9d6-c977-4c7b-a27c-64f9ba8086a7"}
    return localclient.get(addr, params).content


def directions_pdf_result(pks):
    localclient = TC(enforce_csrf_checks=False)
    addr = "/results/pdf"
    params = {"pk": json.dumps(pks), 'leftnone': '1', 'token': "8d63a9d6-c977-4c7b-a27c-64f9ba8086a7", 'withSignatureStamps': '1'}
    result = localclient.get(addr, params).content
    pdf_content = base64.b64encode(result).decode('utf-8')
    return pdf_content
