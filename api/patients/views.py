import datetime
import logging
import re
import threading
from typing import Optional, List

import pytz_deprecation_shim as pytz
import simplejson as json
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email

from api.patients.common_func import get_card_control_param
from ecp_integration.integration import search_patient_ecp_by_person_id
from laboratory.decorators import group_required
from django.core.exceptions import ValidationError
from django.db import transaction, connections
from django.db.models import Prefetch, Q
from django.forms import model_to_dict
from django.http import JsonResponse

from api import sql_func
from appconf.manager import SettingManager
from clients.models import (
    CardBase,
    Individual,
    Card,
    Document,
    DocumentType,
    District,
    AnamnesisHistory,
    DispensaryReg,
    CardDocUsage,
    BenefitReg,
    BenefitType,
    VaccineReg,
    Phones,
    AmbulatoryData,
    AmbulatoryDataHistory,
    DispensaryRegPlans,
    ScreeningRegPlan,
    AdditionalPatientDispensaryPlan,
    CardControlParam,
    PatientHarmfullFactor,
)
from contracts.models import Company, CompanyDepartment, MedicalExamination
from directions.models import Issledovaniya
from directory.models import Researches, PatientControlParam
from laboratory import settings
from laboratory.utils import strdate, start_end_year, localtime
from rmis_integration.client import Client
from slog.models import Log
from statistics_tickets.models import VisitPurpose
from tfoms.integration import match_enp, match_patient, match_patient_by_snils
from directory.models import DispensaryPlan
from utils.data_verification import data_parse


logger = logging.getLogger(__name__)


def full_patient_search_data(p, query):
    dp = re.compile(r'^[0-9]{2}\.[0-9]{2}\.[0-9]{4}$')
    split = str(re.sub(' +', ' ', str(query))).split()
    n = p = ""
    f = split[0]
    rmis_req = {"surname": f + "%"}
    if len(split) > 1:
        n = split[1]
        rmis_req["name"] = n + "%"
    if len(split) > 2:
        if re.search(dp, split[2]):
            split = [split[0], split[1], '', split[2]]
        else:
            p = split[2]
            rmis_req["patrName"] = p + "%"
    if len(split) > 3:
        if '.' in split[3]:
            btday = split[3].split(".")
        elif len(split[3]) == 8 and split[3].isdigit():
            btday = [split[3][0:2], split[3][2:4], split[3][4:8]]
        else:
            btday = None
        if btday:
            if len(btday) == 2 and len(btday[1]) == 6:
                btday = btday[1][2:] + "-" + btday[1][:2] + "-" + btday[0]
            else:
                btday = btday[2] + "-" + btday[1] + "-" + btday[0]
            rmis_req["birthDate"] = btday
    return f, n, p, rmis_req, split


@login_required
def patients_search_card(request):
    objects = []
    data = []
    d = json.loads(request.body)
    inc_rmis = d.get('inc_rmis')
    always_phone_search = d.get('always_phone_search')
    tfoms_module = SettingManager.l2('tfoms')
    birthday_order = SettingManager.l2('birthday_order')
    inc_tfoms = d.get('inc_tfoms') and tfoms_module
    card_type = CardBase.objects.get(pk=d['type'])
    query = d.get('query', '').strip()
    suggests = d.get('suggests', False)
    extended_search = d.get('extendedSearch', False)
    limit = min(int(d.get('limit', 10)), 20)
    form = d.get('form', {})
    p = re.compile(r'^[а-яё]{3}[0-9]{8}$', re.IGNORECASE)
    p2 = re.compile(r'^([А-яЁё\-]+)( ([А-яЁё\-]+)(( ([А-яЁё\-]*))?( ([0-9]{2}\.?[0-9]{2}\.?[0-9]{4}))?)?)?$')
    p_tfoms = re.compile(r'^([А-яЁё\-]+) ([А-яЁё\-]+)( ([А-яЁё\-]+))? (([0-9]{2})\.?([0-9]{2})\.?([0-9]{4}))$')
    p3 = re.compile(r'^[0-9]{1,15}$')
    p_enp_re = re.compile(r'^[0-9]{16}$')
    p_enp = bool(re.search(p_enp_re, query))
    p_snils_re = re.compile(r'^[0-9]{11}$')
    p_snils = bool(re.search(p_snils_re, query))
    p4 = re.compile(r'card_pk:\d+(:(true|false))?', flags=re.IGNORECASE)
    p4i = bool(re.search(p4, query.lower()))
    p5 = re.compile(r'phone:.+')
    p5i = bool(re.search(p5, query))
    p_ecp = re.compile(r'ecp:\d+')
    is_ecp_search = bool(re.search(p_ecp, query))
    pat_bd = re.compile(r"\d{4}-\d{2}-\d{2}")
    c = None
    has_phone_search = False
    inc_archive = form and form.get('archive', False)

    if extended_search and form:
        q = {}

        family = str(form.get('family', ''))
        if family:
            q['family__istartswith'] = family

        name = str(form.get('name', ''))
        if name:
            q['name__istartswith'] = name

        patronymic = str(form.get('patronymic', ''))
        if patronymic:
            q['patronymic__istartswith'] = patronymic

        birthday = str(form.get('birthday', ''))
        if birthday:
            birthday_parts = birthday.split('.')
            if len(birthday_parts) == 3:
                if birthday_parts[0].isdigit():
                    q['birthday__day'] = int(birthday_parts[0])
                if birthday_parts[1].isdigit():
                    q['birthday__month'] = int(birthday_parts[1])
                if birthday_parts[2].isdigit():
                    q['birthday__year'] = int(birthday_parts[2])

        objects = Individual.objects.all()

        if q:
            objects = objects.filter(**q)

        enp_s = str(form.get('enp_s', ''))
        enp_n = str(form.get('enp_n', ''))
        if enp_n:
            if enp_s:
                objects = objects.filter(document__serial=enp_s, document__number=enp_s, document__document_type__title='Полис ОМС')
            else:
                objects = objects.filter(document__number=enp_n, document__document_type__title='Полис ОМС')

        pass_s = str(form.get('pass_s', ''))
        pass_n = str(form.get('pass_n', ''))
        if pass_n:
            objects = objects.filter(document__serial=pass_s, document__number=pass_n, document__document_type__title='Паспорт гражданина РФ')

        snils = str(form.get('snils', ''))
        if snils:
            objects = objects.filter(document__number=snils, document__document_type__title='СНИЛС')

        medbook_number = str(form.get('medbookNumber', ''))
        if medbook_number and SettingManager.l2('profcenter'):
            objects = objects.filter(card__medbook_number=medbook_number)

        phone = str(form.get('phone', ''))

        if phone:
            normalized_phones = Phones.normalize_to_search(phone)
            if normalized_phones:
                objects = objects.filter(
                    Q(card__phones__normalized_number__in=normalized_phones)
                    | Q(card__phones__number__in=normalized_phones)
                    | Q(card__phone__in=normalized_phones)
                    | Q(card__doctorcall__phone__in=normalized_phones)
                )
    if is_ecp_search and query or (query and ":" in query[0]):
        ecp_id = query.split(':')[1]
        patient_data = search_patient_ecp_by_person_id(ecp_id)
        if patient_data and (patient_data.get('PersonSnils_Snils') or patient_data.get('enp')):
            Individual.import_from_ecp(patient_data)
        objects = Individual.objects.filter(ecp_id=ecp_id)
    elif p5i or (always_phone_search and len(query) == 11 and query.isdigit()):
        has_phone_search = True
        phone = query.replace('phone:', '')
        normalized_phones = Phones.normalize_to_search(phone)
        objects = list(
            Individual.objects.filter(
                Q(card__phones__normalized_number__in=normalized_phones)
                | Q(card__phones__number__in=normalized_phones)
                | Q(card__phone__in=normalized_phones)
                | Q(card__doctorcall__phone__in=normalized_phones)
            )
        )
    elif p_enp:
        if tfoms_module and not suggests:
            from_tfoms = match_enp(query)

            if from_tfoms and isinstance(from_tfoms, dict):
                Individual.import_from_tfoms(from_tfoms)

        objects = list(Individual.objects.filter(document__number=query, document__document_type__title='Полис ОМС'))
    elif p_snils:
        if tfoms_module and not suggests:
            from_tfoms = match_patient_by_snils(query)
            if from_tfoms and len(from_tfoms) == 1 and isinstance(from_tfoms[0], dict):
                Individual.import_from_tfoms(from_tfoms)

        objects = list(Individual.objects.filter(document__number=query, document__document_type__title='СНИЛС'))
    elif not p4i:
        if inc_tfoms:
            t_parts = re.search(p_tfoms, query.lower()).groups()
            t_bd = "{}-{}-{}".format(t_parts[7], t_parts[6], t_parts[5])

            from_tfoms = match_patient(t_parts[0], t_parts[1], t_parts[2], t_bd)

            if isinstance(from_tfoms, list):
                for t_row in from_tfoms:
                    if isinstance(t_row, dict):
                        Individual.import_from_tfoms(t_row, no_update=True)

        if re.search(p, query.lower()):
            initials = query[0:3].upper()
            btday = query[7:11] + "-" + query[5:7] + "-" + query[3:5]
            if not pat_bd.match(btday):
                return JsonResponse([], safe=False)
            try:
                objects = list(
                    Individual.objects.filter(family__startswith=initials[0], name__startswith=initials[1], patronymic__startswith=initials[2], birthday=btday, card__base=card_type)
                )
                if ((card_type.is_rmis and len(objects) == 0) or (card_type.internal_type and inc_rmis)) and not suggests:
                    # c = Client(modules="patients")
                    # objects += c.patients.import_individual_to_base({"surname": query[0] + "%", "name": query[1] + "%", "patrName": query[2] + "%", "birthDate": btday}, fio=True)
                    pass
            except Exception as e:
                logger.exception(e)
        elif re.search(p2, query):
            f, n, p, rmis_req, split = full_patient_search_data(p, query)

            if len(split) > 3 or (len(split) == 3 and split[-1].isdigit()):
                sbd = split[-1]
                if len(sbd) == 8:
                    sbd = "{}.{}.{}".format(sbd[0:2], sbd[2:4], sbd[4:8])

                objects = Individual.objects.filter(family__istartswith=f, name__istartswith=n, card__base=card_type, birthday=datetime.datetime.strptime(sbd, "%d.%m.%Y").date())

                if len(split) > 3:
                    objects.filter(patronymic__istartswith=p)

                objects = objects[:10]
            else:
                objects = Individual.objects.filter(family__istartswith=f, name__istartswith=n, patronymic__istartswith=p, card__base=card_type)[:10]

            if ((card_type.is_rmis and (len(objects) == 0 or (len(split) < 4 and len(objects) < 10))) or (card_type.internal_type and inc_rmis)) and not suggests:
                objects = list(objects)
                try:
                    if not c:
                        pass
                        # c = Client(modules="patients")
                    # objects += c.patients.import_individual_to_base(rmis_req, fio=True, limit=10 - len(objects))
                except Exception as e:
                    logger.exception(e)

        if (
            (re.search(p3, query) and not card_type.is_rmis)
            or (len(objects) == 0 and len(query) == 16 and not p_enp and card_type.internal_type)
            or (card_type.is_rmis and not re.search(p3, query))
        ):
            resync = True
            if len(objects) == 0:
                resync = False
                try:
                    objects = Individual.objects.filter(card__number=query.upper(), card__base=card_type)
                    if not inc_archive:
                        objects = objects.filter(card__is_archive=False)
                    objects = list(objects)
                    if (card_type.is_rmis or card_type.internal_type) and len(objects) == 0 and len(query) == 16 and not suggests:
                        if not c:
                            c = Client(modules="patients")
                        objects += c.patients.import_individual_to_base(query)
                    elif not suggests:
                        resync = True
                except Exception as e:
                    logger.exception(e)
            if resync and card_type.is_rmis and not suggests:
                if not c:
                    c = Client(modules="patients")

                sema = threading.BoundedSemaphore(10)
                threads = list()

                def sync_i(ind_local: Individual, client: Client):
                    sema.acquire()
                    try:
                        ind_local.sync_with_rmis(c=client)
                    finally:
                        sema.release()

                    try:
                        connections.close_all()
                        logger.exception("Closed db connections")
                    except Exception as e:
                        logger.exception(f"Error closing connections {e}")

                for obj in objects:
                    thread = threading.Thread(target=sync_i, args=(obj, c))
                    threads.append(thread)
                    thread.start()

    if p4i:
        parts = query.split(":")
        cards = Card.objects.filter(pk=int(parts[1]))
        inc_archive = inc_archive or (len(parts) > 2 and parts[2] == 'true')
    else:
        cards = Card.objects.filter(base=card_type, individual__in=objects)
        
        if not has_phone_search and not p_snils and re.match(p3, query):
            cards = cards.filter(number=query)

    if p_enp and cards:
        cards = cards.filter(carddocusage__document__number=query, carddocusage__document__document_type__title='Полис ОМС')

    if cards:
        medbook_number = str(form.get('medbookNumber', ''))
        if medbook_number and SettingManager.l2('profcenter'):
            cards = cards.filter(medbook_number=medbook_number)

    d1, d2 = start_end_year()

    if birthday_order:
        cards = cards.order_by('-individual__birthday')

    if not inc_archive:
        cards = cards.filter(is_archive=False)
    row: Card
    for row in (
        cards.select_related("individual", "base")
        .prefetch_related(
            Prefetch(
                'individual__document_set',
                queryset=Document.objects.filter(is_active=True, document_type__title__in=['СНИЛС', 'Паспорт гражданина РФ', 'Полис ОМС'])
                .distinct("pk", "number", "document_type", "serial")
                .select_related('document_type')
                .order_by('pk'),
            ),
            'phones_set',
        )
        .distinct()[:limit]
    ):
        disp_data = sql_func.dispensarization_research(row.individual.sex, row.individual.age_for_year(), row.pk, d1, d2)

        status_disp = 'finished'
        if not disp_data:
            status_disp = 'notneed'
        else:
            for i in disp_data:
                if not i[4]:
                    status_disp = 'need'
                    break

        data.append(
            {
                "type_title": card_type.title,
                "base_pk": row.base_id,
                "num": row.number,
                "is_rmis": row.base.is_rmis,
                "family": row.individual.family,
                "name": row.individual.name,
                "twoname": row.individual.patronymic,
                "birthday": row.individual.bd(),
                "age": row.individual.age_s(),
                "fio_age": row.individual.fio(full=True),
                "sex": row.individual.sex,
                "individual_pk": row.individual_id,
                "isArchive": row.is_archive,
                "pk": row.pk,
                "phones": Phones.phones_to_normalized_list(row.phones_set.all(), row.phone),
                "main_diagnosis": row.main_diagnosis,
                "docs": [
                    *[
                        {
                            "pk": x.pk,
                            "type_title": x.document_type.title,
                            "document_type_id": x.document_type_id,
                            "serial": x.serial,
                            "number": x.number,
                            "is_active": x.is_active,
                            "date_start": x.date_start,
                            "date_end": x.date_end,
                            "who_give": x.who_give,
                            "from_rmis": x.from_rmis,
                            "rmis_uid": x.rmis_uid,
                        }
                        for x in row.individual.document_set.all()
                    ],
                    *(
                        [
                            {
                                "pk": -10,
                                "type_title": "Номер мед.книжки",
                                "document_type_id": -10,
                                "serial": row.medbook_prefix,
                                "number": str(row.medbook_number),
                                "is_active": True,
                                "date_start": None,
                                "date_end": None,
                                "who_give": "",
                                "from_rmis": False,
                                "rmis_uid": None,
                            }
                        ]
                        if row.medbook_number
                        else []
                    ),
                ],
                "medbookNumber": f"{row.medbook_prefix} {row.medbook_number}".strip(),
                "status_disp": status_disp,
                "disp_data": disp_data,
            }
        )
    return JsonResponse({"results": data})


@login_required
def patients_search_individual(request):
    objects = []
    data = []
    d = json.loads(request.body)
    query = d['query'].strip()
    p = re.compile(r'[а-яё]{3}[0-9]{8}', re.IGNORECASE)
    p2 = re.compile(r'^([А-яЁё\-]+)( ([А-яЁё\-]+)(( ([А-яЁё\-]*))?( ([0-9]{2}\.[0-9]{2}\.[0-9]{4}))?)?)?$')
    p4 = re.compile(r'individual_pk:\d+')
    pat_bd = re.compile(r"\d{4}-\d{2}-\d{2}")
    if re.search(p, query.lower()):
        initials = query[0:3].upper()
        btday = query[7:11] + "-" + query[5:7] + "-" + query[3:5]
        if not pat_bd.match(btday):
            return JsonResponse([], safe=False)
        try:
            objects = Individual.objects.filter(family__startswith=initials[0], name__startswith=initials[1], patronymic__startswith=initials[2], birthday=btday)
        except ValidationError:
            objects = []
    elif re.search(p2, query):
        f, n, p, rmis_req, split = full_patient_search_data(p, query)
        objects = Individual.objects.filter(family__istartswith=f, name__istartswith=n, patronymic__istartswith=p)
        if len(split) > 3:
            objects = Individual.objects.filter(family__istartswith=f, name__istartswith=n, patronymic__istartswith=p, birthday=datetime.datetime.strptime(split[3], "%d.%m.%Y").date())

    if re.search(p4, query):
        objects = Individual.objects.filter(pk=int(query.split(":")[1]))
    n = 0

    if not isinstance(objects, list):
        for row in objects.distinct().order_by("family", "name", "patronymic", "birthday"):
            n += 1
            data.append({"family": row.family, "name": row.name, "patronymic": row.patronymic, "birthday": row.bd(), "age": row.age_s(), "sex": row.sex, "pk": row.pk})
            if n == 25:
                break
    return JsonResponse({"results": data})


def patients_search_l2_card(request):
    data = []
    request_data = json.loads(request.body)

    cards = Card.objects.filter(pk=request_data.get('card_pk', -1))
    if cards.exists():
        card_orig = cards[0]
        Card.add_l2_card(card_orig=card_orig)
        l2_cards = Card.objects.filter(individual=card_orig.individual, base__internal_type=True)

        for row in l2_cards.filter(is_archive=False):
            docs = (
                Document.objects.filter(individual__pk=row.individual_id, is_active=True, document_type__title__in=['СНИЛС', 'Паспорт гражданина РФ', 'Полис ОМС'])
                .distinct("pk", "number", "document_type", "serial")
                .order_by('pk')
            )
            data.append(
                {
                    "type_title": row.base.title,
                    "num": row.number,
                    "is_rmis": row.base.is_rmis,
                    "family": row.individual.family,
                    "name": row.individual.name,
                    "twoname": row.individual.patronymic,
                    "birthday": row.individual.bd(),
                    "age": row.individual.age_s(),
                    "sex": row.individual.sex,
                    "individual_pk": row.individual_id,
                    "base_pk": row.base_id,
                    "pk": row.pk,
                    "phones": row.get_phones(),
                    "docs": [{**model_to_dict(x), "type_title": x.document_type.title} for x in docs],
                    "main_diagnosis": row.main_diagnosis,
                }
            )
    return JsonResponse({"results": data})


@login_required
def patients_get_card_data(request, card_id):
    card = Card.objects.get(pk=card_id)
    c = model_to_dict(card)
    i = model_to_dict(card.individual)
    docs = [
        {**model_to_dict(x), "type_title": x.document_type.title}
        for x in Document.objects.filter(individual=card.individual).distinct('pk', "number", "document_type", "serial").order_by('pk')
    ]
    rc = Card.objects.filter(base__is_rmis=True, individual=card.individual)
    d = District.objects.all().order_by('-sort_weight', '-id')

    age = card.individual.age()
    if age < 14:
        doc_types = [{"pk": x.pk, "title": x.title} for x in DocumentType.objects.all().exclude(title__startswith="Паспорт гражданина РФ")]
    else:
        doc_types = [{"pk": x.pk, "title": x.title} for x in DocumentType.objects.all()]
    return JsonResponse(
        {
            **i,
            **c,
            "docs": docs,
            "main_docs": card.get_card_documents(),
            "main_address_full": card.main_address_full,
            "fact_address_full": card.fact_address_full,
            "has_rmis_card": rc.exists(),
            "custom_workplace": card.work_place != "",
            "work_place_db": card.work_place_db_id or -1,
            "room_location_db": card.room_location_id if card.room_location_id else -1,
            "work_place_db_title": card.work_place_db.title if card.work_place_db else "",
            "work_department_db": card.work_department_db.pk if card.work_department_db else -1,
            "district": card.district_id or -1,
            "districts": [{"id": -1, "title": "НЕ ВЫБРАН"}, *[{"id": x.pk, "title": x.title} for x in d.filter(is_ginekolog=False)]],
            "ginekolog_district": card.ginekolog_district_id or -1,
            "gin_districts": [{"id": -1, "title": "НЕ ВЫБРАН"}, *[{"id": x.pk, "title": x.title} for x in d.filter(is_ginekolog=True)]],
            "agent_types": [{"key": x[0], "title": x[1]} for x in Card.AGENT_CHOICES if x[0]],
            "excluded_types": Card.AGENT_CANT_SELECT,
            "agent_need_doc": Card.AGENT_NEED_DOC,
            "mother": None if not card.mother else card.mother.get_fio_w_card(),
            "mother_pk": card.mother_id,
            "father": None if not card.father else card.father.get_fio_w_card(),
            "father_pk": card.father_id,
            "curator": None if not card.curator else card.curator.get_fio_w_card(),
            "curator_pk": card.curator_id,
            "agent": None if not card.agent else card.agent.get_fio_w_card(),
            "agent_pk": card.agent_id,
            "payer": None if not card.payer else card.payer.get_fio_w_card(),
            "payer_pk": card.payer_id,
            "rmis_uid": rc[0].number if rc.exists() else None,
            "doc_types": doc_types,
            "number_poli": card.number_poliklinika,
            "harmful": card.harmful_factor,
            "medbookPrefix": card.medbook_prefix,
            "medbookNumber": card.medbook_number,
            "medbookNumberCustom": card.medbook_number if card.medbook_type == 'custom' else '',
            "medbookNumberCustomOriginal": card.medbook_number if card.medbook_type == 'custom' else '',
            "medbookType": card.medbook_type,
            "medbookTypePrev": card.medbook_type,
            "isArchive": card.is_archive,
            "contactTrustHealth": card.contact_trust_health,
        }
    )


@login_required
def patients_get_card_simple_data(request, card_id):
    card = Card.objects.get(pk=card_id)
    base = card.base
    individual = card.individual

    return JsonResponse(
        {
            "pk": card_id,
            "age": individual.age_s(),
            "base": {"pk": base.pk, "title": base.title, "short_title": base.short_title, "internal_type": base.internal_type},
            "birthday": individual.bd(),
            "family": individual.family,
            "name": individual.name,
            "twoname": individual.patronymic,
            "patronymic": individual.patronymic,
            "individual_pk": individual.pk,
            "isArchive": card.is_archive,
            "main_diagnosis": card.main_diagnosis,
        }
    )


@login_required
@group_required("Картотека L2", "Лечащий врач", "Врач-лаборант", "Оператор лечащего врача", "Оператор Контакт-центра")
def patients_card_save(request):
    request_data = json.loads(request.body)
    message = ""
    messages = []

    for field in ['family', 'name', 'patronymic']:
        request_data[field] = request_data[field].strip()

    if "new_individual" in request_data and (request_data["new_individual"] or not Individual.objects.filter(pk=request_data["individual_pk"])) and request_data["card_pk"] < 0:
        i = Individual(family=request_data["family"], name=request_data["name"], patronymic=request_data["patronymic"], birthday=request_data["birthday"], sex=request_data["sex"])
        i.save()
    else:
        changed = False
        i = Individual.objects.get(pk=request_data["individual_pk"] if request_data["card_pk"] < 0 else Card.objects.get(pk=request_data["card_pk"]).individual_id)
        if (
            i.family != request_data["family"]
            or i.name != request_data["name"]
            or i.patronymic != request_data["patronymic"]
            or str(i.birthday) != request_data["birthday"]
            or i.sex != request_data["sex"]
        ):
            changed = True
        i.family = request_data["family"]
        i.name = request_data["name"]
        i.patronymic = request_data["patronymic"]
        i.birthday = datetime.datetime.strptime(request_data["birthday"], "%d.%m.%Y" if '.' in request_data["birthday"] else "%Y-%m-%d").date()
        i.sex = request_data["sex"]
        i.save()
        if Card.objects.filter(individual=i, base__is_rmis=True).exists() and changed:
            try:
                c = Client(modules=["individuals", "patients"])
                c.patients.send_patient(Card.objects.filter(individual=i, base__is_rmis=True)[0])
            except:
                messages.append("Синхронизация с РМИС не удалась")

    individual_pk = i.pk

    if request_data["card_pk"] < 0:
        with transaction.atomic():
            base = CardBase.objects.select_for_update().get(pk=request_data["base_pk"], internal_type=True)
            c = Card(number=Card.next_l2_n(), base=base, individual=i, main_diagnosis="", main_address="", fact_address="")
            c.save()
            card_pk = c.pk
        Log.log(card_pk, 30000, request.user.doctorprofile, request_data)
    else:
        card_pk = request_data["card_pk"]
        c = Card.objects.get(pk=card_pk)
        individual_pk = request_data["individual_pk"]
    c.main_diagnosis = request_data["main_diagnosis"]

    try:
        vals = json.loads(request_data["main_address_full"])
        c.main_address = vals['address']
        c.main_address_fias = vals['fias']
        c.main_address_details = vals['details']
    except:
        c.main_address = request_data["main_address"]
        c.main_address_fias = None
        c.main_address_details = None

    try:
        vals = json.loads(request_data["fact_address_full"])
        c.fact_address = vals['address']
        c.fact_address_fias = vals['fias']
        c.fact_address_details = vals['details']
    except:
        c.fact_address = request_data["fact_address"]
        c.fact_address_fias = None
        c.fact_address_details = None
    if request_data["custom_workplace"] or not Company.objects.filter(pk=request_data.get("work_place_db", -1)).exists():
        c.work_place_db = None
        c.work_place = request_data["work_place"] if request_data["custom_workplace"] else ''
    else:
        c.work_place_db = Company.objects.get(pk=request_data["work_place_db"])
        c.work_place = ''
    if not CompanyDepartment.objects.filter(pk=request_data.get("work_department_db", -1)).exists():
        c.work_department_db = None
    else:
        c.work_department_db = CompanyDepartment.objects.filter(pk=request_data["work_department_db"]).first()
    c.district_id = request_data["district"] if request_data["district"] != -1 else None
    c.ginekolog_district_id = request_data["gin_district"] if request_data["gin_district"] != -1 else None
    c.work_position = request_data["work_position"]
    c.work_department = request_data["work_department"]
    c.phone = request_data["phone"]
    c.email = request_data.get("email", "")
    c.send_to_email = bool(request_data.get("send_to_email", False))
    c.harmful_factor = request_data.get("harmful", "")
    c.contact_trust_health = request_data.get("contactTrustHealth", "")
    medbook_type = request_data.get("medbookType", "")
    medbook_prefix = str(request_data.get("medbookPrefix", "")).strip()
    medbook_number = str(request_data.get("medbookNumber", "-1"))
    medbook_number_custom = str(request_data.get("medbookNumberCustom", "-1"))
    medbook_number = medbook_number if medbook_type != 'custom' else medbook_number_custom
    medbook_number_int = int(medbook_number) if medbook_number.isdigit() else None
    if medbook_type == 'none' and c.medbook_type != 'none':
        c.medbook_number = ''
        c.medbook_type = medbook_type
    else:
        try:
            with transaction.atomic():
                base = CardBase.objects.select_for_update().get(pk=request_data["base_pk"], internal_type=True)
                if medbook_type == 'custom' and medbook_number_int is not None and (c.medbook_number != medbook_number_int or c.medbook_prefix != medbook_prefix):
                    medbook_auto_start = SettingManager.get_medbook_auto_start()
                    if medbook_number_int <= 1 or medbook_auto_start <= medbook_number_int:
                        raise Exception("Некорректный номер мед.книжки")
                    if Card.objects.filter(medbook_number=medbook_number, base=base, medbook_prefix=medbook_prefix).exclude(pk=c.pk).exists():
                        raise Exception(f"Номер {medbook_prefix} {medbook_number} уже есть у другого пациента")
                    c.medbook_prefix = medbook_prefix
                    c.medbook_number = medbook_number_int
                    c.medbook_type = medbook_type
                elif (c.medbook_type != 'auto' or c.medbook_number == '') and medbook_type == 'auto':
                    c.medbook_prefix = ''
                    c.medbook_number = Card.next_medbook_n()
                    c.medbook_type = medbook_type
        except Exception as e:
            logger.exception(e)
            messages.append(str(e))
    number_poli = request_data.get("number_poli", "")
    if number_poli:
        card_number_poli = Card.objects.filter(number_poliklinika=number_poli)
        for cnp in card_number_poli:
            if cnp.number_poliklinika == number_poli and cnp != c:
                messages.append("Номер карты ТФОМС занят")
                return JsonResponse({"result": "false", "message": message, "messages": messages, "card_pk": card_pk, "individual_pk": individual_pk})
    c.number_poliklinika = number_poli
    if request_data.get("room_location_db") and request_data.get("room_location_db") != -1:
        c.room_location_id = int(request_data.get("room_location_db"))
    else:
        c.room_location = None
    c.save()
    if c.individual.primary_for_rmis:
        try:
            c.individual.sync_with_rmis()
        except:
            messages.append("Синхронизация с РМИС не удалась")
    result = "ok"
    return JsonResponse({"result": result, "message": message, "messages": messages, "card_pk": card_pk, "individual_pk": individual_pk})


@login_required
@group_required("Управление иерархией истории")
def patients_card_archive(request):
    request_data = json.loads(request.body)
    pk = request_data['pk']
    card = Card.objects.get(pk=pk)
    card.is_archive = True
    card.save()
    return JsonResponse({"ok": True})


@login_required
@group_required("Управление иерархией истории")
def patients_card_unarchive(request):
    request_data = json.loads(request.body)
    pk = request_data['pk']
    card = Card.objects.get(pk=pk)
    if card.is_archive:
        n = card.number
        if Card.objects.filter(number=n, is_archive=False, base=card.base).exists():
            return JsonResponse({"ok": False, "message": "fНомер {n} уже занят другой картой"})
        card.is_archive = False
        card.save()
    return JsonResponse({"ok": True})


@login_required
def patients_harmful_factors(request):
    request_data = json.loads(request.body)
    pk = request_data['card_pk']
    card = Card.objects.get(pk=pk)
    rows = PatientHarmfullFactor.get_card_harmful_factor(card)
    return JsonResponse(rows, safe=False)


@login_required
def patients_save_harmful_factors(request):
    request_data = json.loads(request.body)
    tb_data = request_data.get('tb_data', '')
    card_pk = int(request_data.get('card_pk', -1))
    date_med_exam = request_data.get('dateMedExam')
    if len(tb_data) < 1:
        return JsonResponse({'message': 'Ошибка в количестве'})
    if date_med_exam:
        MedicalExamination.update_date(card_pk, date_med_exam)
    result = PatientHarmfullFactor.save_card_harmful_factor(card_pk, tb_data)
    if result:
        return JsonResponse({'ok': True, 'message': 'Сохранено'})
    return JsonResponse({'ok': False, 'message': 'ошибка'})


def individual_search(request):
    result = []
    request_data = json.loads(request.body)
    tfoms_module = SettingManager.l2('tfoms')
    family = request_data["family"]
    name = request_data["name"]
    patronymic = request_data["patronymic"]
    birthday = request_data["birthday"]
    forced_gender = []

    if tfoms_module and family and name and birthday:
        from_tfoms = match_patient(family, name, patronymic, birthday)

        for row in from_tfoms:
            Individual.import_from_tfoms(row, no_update=True)
            forced_gender.append(row['gender'].lower())

    for i in Individual.objects.filter(family=family, name=name, patronymic=patronymic, birthday=birthday):
        result.append(
            {
                "pk": i.pk,
                "fio": i.fio(full=True),
                "docs": [
                    {**model_to_dict(x), "type_title": x.document_type.title}
                    for x in Document.objects.filter(individual=i, is_active=True).distinct("number", "document_type", "serial", "date_end", "date_start")
                ],
                "l2_cards": [{"number": x.number, "pk": x.pk} for x in Card.objects.filter(individual=i, base__internal_type=True, is_archive=False)],
            }
        )
        forced_gender.append(i.sex)

    forced_gender = None if not forced_gender or forced_gender.count(forced_gender[0]) != len(forced_gender) else forced_gender[0]

    return JsonResponse({"result": result, 'forced_gender': forced_gender})


def get_sex_by_param(request):
    request_data = json.loads(request.body)
    t = request_data.get("t")
    v = request_data.get("v", "")
    r = "м"
    if t == "name":
        p = Individual.objects.filter(name=v)
        r = "м" if p.filter(sex__iexact="м").count() >= p.filter(sex__iexact="ж").count() else "ж"
    if t == "family":
        p = Individual.objects.filter(family=v)
        r = "м" if p.filter(sex__iexact="м").count() >= p.filter(sex__iexact="ж").count() else "ж"
    if t == "patronymic":
        p = Individual.objects.filter(patronymic=v)
        r = "м" if p.filter(sex__iexact="м").count() >= p.filter(sex__iexact="ж").count() else "ж"
    return JsonResponse({"sex": r})


def edit_doc(request):
    request_data = json.loads(request.body)
    pk = request_data["pk"]
    serial = request_data["serial"].strip()
    number = request_data["number"].strip()
    type_o = DocumentType.objects.get(pk=request_data["type"])
    is_active = request_data["is_active"]
    date_start = request_data["date_start"]
    date_start = None if date_start == "" else date_start
    date_end = request_data["date_end"]
    date_end = None if date_end == "" else date_end
    who_give = (request_data["who_give"] or "").strip()

    if pk == -1:
        card = Card.objects.get(pk=request_data["card_pk"])
        d = Document(
            document_type=type_o,
            number=number,
            serial=serial,
            from_rmis=False,
            date_start=date_start,
            date_end=date_end,
            who_give=who_give,
            is_active=is_active,
            individual=Individual.objects.get(pk=request_data["individual_pk"]),
        )
        d.save()
        cdu = CardDocUsage.objects.filter(card=card, document__document_type=type_o)
        if not cdu.exists():
            CardDocUsage(card=card, document=d).save()
        else:
            for c in cdu:
                c.document = d
                c.save(update_fields=["document"])
        Log.log(d.pk, 30002, request.user.doctorprofile, request_data)
    else:
        for d in Document.objects.filter(pk=pk, from_rmis=False):
            d.number = number
            d.serial = serial
            d.is_active = is_active
            d.date_start = date_start
            d.date_end = date_end
            d.who_give = who_give
            d.save()
        Log.log(pk, 30002, request.user.doctorprofile, request_data)
        d = Document.objects.get(pk=pk)

    try:
        d.sync_rmis()
    except Exception as e:
        print('RMIS error', e)  # noqa: T001

    return JsonResponse({"ok": True})


def update_cdu(request):
    request_data = json.loads(request.body)
    card = Card.objects.get(pk=request_data["card_pk"])
    doc = Document.objects.get(pk=request_data["doc"])
    cdu = CardDocUsage.objects.filter(card=card, document__document_type=doc.document_type)
    if not cdu.exists():
        CardDocUsage(card=card, document=doc).save()
    else:
        for c in cdu:
            c.document = doc
            c.save(update_fields=["document"])
    Log.log(card.pk, 30004, request.user.doctorprofile, request_data)

    return JsonResponse({"ok": True})


def sync_rmis(request):
    request_data = json.loads(request.body)
    card = Card.objects.get(pk=request_data["card_pk"])
    card.individual.sync_with_rmis()
    return JsonResponse({"ok": True})


def sync_ecp(request):
    request_data = json.loads(request.body)
    card = Card.objects.get(pk=request_data["card_pk"])
    card.individual.sync_with_rmis()
    return JsonResponse({"ok": True})


def sync_tfoms(request):
    request_data = json.loads(request.body)
    card = Card.objects.get(pk=request_data["card_pk"])
    is_new, updated = card.individual.sync_with_tfoms()
    return JsonResponse({"ok": True, "is_new": is_new, "updated": updated})


def update_wia(request):
    request_data = json.loads(request.body)
    card = Card.objects.get(pk=request_data["card_pk"])
    key = request_data["key"]
    if key in [x[0] for x in Card.AGENT_CHOICES]:
        card.who_is_agent = key
        card.save()
        Log.log(card.pk, 30006, request.user.doctorprofile, request_data)

    return JsonResponse({"ok": True})


def edit_agent(request):
    request_data = json.loads(request.body)
    key = request_data["key"]
    card = None if not request_data["card_pk"] else Card.objects.get(pk=request_data["card_pk"])
    parent_card = Card.objects.filter(pk=request_data["parent_card_pk"])
    doc = request_data["doc"] or ''
    clear = request_data["clear"]
    need_doc = key in Card.AGENT_NEED_DOC

    upd = {}

    if clear or not card:
        upd[key] = None
        if need_doc:
            upd[key + "_doc_auth"] = ''
        if parent_card[0].who_is_agent == key:
            upd["who_is_agent"] = ''
    else:
        upd[key] = card
        if need_doc:
            upd[key + "_doc_auth"] = doc
        if key not in Card.AGENT_CANT_SELECT:
            upd["who_is_agent"] = key

    for card in parent_card:
        for k, v in upd.items():
            setattr(card, k, v)

        card.save(update_fields=list(upd.keys()))

    Log.log(request_data["parent_card_pk"], 30005, request.user.doctorprofile, request_data)

    return JsonResponse({"ok": True})


def load_dreg(request):
    request_data = json.loads(request.body)
    data = []
    diagnoses = set()
    for a in DispensaryReg.objects.filter(card__pk=request_data["card_pk"]).order_by('date_start', 'pk'):
        data.append(
            {
                "pk": a.pk,
                "diagnos": a.diagnos,
                "illnes": a.illnes,
                "spec_reg": '' if not a.spec_reg else a.spec_reg.title,
                "doc_start_reg": '' if not a.doc_start_reg else a.doc_start_reg.get_fio(),
                "doc_start_reg_id": a.doc_start_reg_id,
                "date_start": '' if not a.date_start else strdate(a.date_start),
                "doc_end_reg": '' if not a.doc_end_reg else a.doc_end_reg.get_fio(),
                "doc_end_reg_id": a.doc_end_reg_id,
                "date_end": '' if not a.date_end else strdate(a.date_end),
                "why_stop": a.why_stop,
            }
        )
        if not a.date_end:
            diagnoses.add(a.diagnos)

    researches = []
    specialities = []
    researches_data = []
    specialities_data = []
    card = Card.objects.get(pk=request_data["card_pk"])
    visits = VisitPurpose.objects.filter(title__icontains="диспансерн")
    year = request_data.get('year', '2020')
    unique_research_pk = []
    for d in sorted(diagnoses):
        need = DispensaryPlan.objects.filter(diagnos=d)
        for i in need:
            if i.research:
                if i.research not in researches:
                    researches.append(i.research)
                    unique_research_pk.append(i.research.pk)
                    results = research_last_result_every_month([i.research], card, year)
                    plans = get_dispensary_reg_plans(card, i.research, None, year)
                    researches_data.append(
                        {
                            "type": "research",
                            "research_title": i.research.title,
                            "research_pk": i.research.pk,
                            "assign_research_pk": i.research.pk,
                            "assignment": False,
                            "diagnoses_time": [],
                            "results": results,
                            "plans": plans,
                            "max_time": 1,
                            "times": len([x for x in results if x]),
                        }
                    )
                index_res = researches.index(i.research)
                researches_data[index_res]['diagnoses_time'].append({"diagnos": i.diagnos, "times": i.repeat})
            if i.speciality:
                if i.speciality not in specialities:
                    specialities.append(i.speciality)
                    results = research_last_result_every_month(Researches.objects.filter(speciality=i.speciality), request_data["card_pk"], year, visits)
                    plans = get_dispensary_reg_plans(card, None, i.speciality, year)
                    spec_assign_research = Researches.objects.filter(speciality=i.speciality).first()
                    specialities_data.append(
                        {
                            "type": "speciality",
                            "research_title": i.speciality.title,
                            "research_pk": i.speciality.pk,
                            "assign_research_pk": spec_assign_research.pk if spec_assign_research else None,
                            "assignment": False,
                            "diagnoses_time": [],
                            "results": results,
                            "plans": plans,
                            "max_time": 1,
                            "times": len([x for x in results if x]),
                        }
                    )
                index_spec = specialities.index(i.speciality)
                specialities_data[index_spec]['diagnoses_time'].append({"diagnos": i.diagnos, "times": i.repeat})

    researches_data.extend(specialities_data)

    # Индивидуальный план
    researches = []
    need = AdditionalPatientDispensaryPlan.objects.filter(card=card)
    for i in need:
        if i.research:
            if i.research not in researches:
                researches.append(i.research)
                results = research_last_result_every_month([i.research], card, year)
                plans = get_dispensary_reg_plans(card, i.research, None, year)
                researches_data.append(
                    {
                        "type": "research",
                        "research_title": i.research.title,
                        "research_pk": i.research.pk,
                        "assign_research_pk": i.research.pk,
                        "assignment": False,
                        "diagnoses_time": [{"diagnos": "И.П.Н.", "times": i.repeat}],
                        "results": results,
                        "plans": plans,
                        "max_time": 1,
                        "times": len([x for x in results if x]),
                    }
                )

    return JsonResponse({"rows": data, "researches_data": researches_data, "year": year, "unique_research_pk": unique_research_pk})


def load_screening(request):
    card_pk: int = data_parse(request.body, {'cardPk': int})[0]
    screening = ScreeningRegPlan.get_screening_data(card_pk)

    return JsonResponse({"data": screening})


def load_control_param(request):
    request_data = json.loads(request.body)
    card_pk = request_data.get("card_pk") or None
    start_date = request_data["start_year"]
    end_date = request_data["end_year"]

    if not (card_pk and start_date and end_date):
        return JsonResponse({"results": ""})
    unique_month_result = get_card_control_param(card_pk, start_date, end_date)
    return JsonResponse({"results": unique_month_result})


def load_selected_control_params(request):
    request_data = json.loads(request.body)
    card_pk = request_data.get("card_pk") or None
    data_params = CardControlParam.get_patient_control_param(card_pk)
    control_param = PatientControlParam.get_contol_param_in_system()
    for element in control_param:
        if not data_params.get(element["id"]):
            data_params[element["id"]] = {"title": element["title"], "selected": False, "isGlobal": False}
    result = [{"id": k, "title": v.get("title", ""), "isSelected": v.get("selected", False), "isGlobal": v.get("isGlobal", False)} for k, v in data_params.items()]
    return JsonResponse({"results": result})


def save_patient_control_params(request):
    request_data = json.loads(request.body)
    card_pk = request_data.get("card_pk") or None
    selected_params = request_data.get("selectedParams") or None
    CardControlParam.save_patient_control_param(card_pk, selected_params)
    return JsonResponse({"ok": True})


def research_last_result_every_month(researches: List[Researches], card: Card, year: str, visits: Optional[List[VisitPurpose]] = None):
    results = []
    filter = {
        "napravleniye__client": card,
        "research__in": researches,
        "time_confirmation__year": year,
    }

    if visits:
        filter['purpose__in'] = visits

    for i in range(12):
        i += 1
        iss: Optional[Issledovaniya] = Issledovaniya.objects.filter(**filter, time_confirmation__month=str(i)).order_by("-time_confirmation").first()
        if iss:
            date = str(localtime(iss.time_confirmation).day).rjust(2, '0')
            results.append({"pk": iss.napravleniye_id, "date": date})
        else:
            results.append(None)

    return results


def get_dispensary_reg_plans(card, research, speciality, year):
    plan = [''] * 12
    disp_plan = DispensaryRegPlans.objects.filter(card=card, research=research, speciality=speciality, date__year=year)
    for d in disp_plan:
        if d.date:
            plan[d.date.month - 1] = str(d.date.day).rjust(2, '0')

    return plan


def update_dispensary_reg_plans(request):
    request_data = json.loads(request.body)
    DispensaryRegPlans.update_plan(request_data["card_pk"], request_data["researches_data_def"], request_data["researches_data"], request_data["year"])

    return JsonResponse({"ok": True})


def update_screening_reg_plan(request):
    request_data = json.loads(request.body)

    ScreeningRegPlan.update_plan(request_data)

    return JsonResponse({"ok": True})


def validate_email_view(request):
    request_data = json.loads(request.body)
    email = request_data['email']

    try:
        if email:
            validate_email(email)
            return JsonResponse({"ok": True})
    except:
        pass

    return JsonResponse({"ok": False})


def load_vaccine(request):
    request_data = json.loads(request.body)
    data = []
    for a in VaccineReg.objects.filter(card__pk=request_data["card_pk"]).order_by('date', 'pk'):
        data.append({"pk": a.pk, "date": strdate(a.date) if a.date else '', "title": a.title, "series": a.series, "amount": a.amount, "method": a.method, "step": a.step, "tap": a.tap})
    return JsonResponse({"rows": data})


def load_ambulatory_data(request):
    request_data = json.loads(request.body)
    data = []
    for a in AmbulatoryData.objects.filter(card__pk=request_data["card_pk"]).order_by('date', 'pk'):
        data.append({"pk": a.pk, "date": strdate(a.date) if a.date else '', "data": a.data})

    return JsonResponse({"rows": data})


def load_benefit(request):
    request_data = json.loads(request.body)
    data = []
    for a in BenefitReg.objects.filter(card__pk=request_data["card_pk"]).order_by('date_start', 'pk'):
        data.append(
            {
                "pk": a.pk,
                "benefit": str(a.benefit),
                "registration_basis": a.registration_basis,
                "doc_start_reg": '' if not a.doc_start_reg else a.doc_start_reg.get_fio(),
                "doc_start_reg_id": a.doc_start_reg_id,
                "date_start": '' if not a.date_start else strdate(a.date_start),
                "doc_end_reg": '' if not a.doc_end_reg else a.doc_end_reg.get_fio(),
                "doc_end_reg_id": a.doc_end_reg_id,
                "date_end": '' if not a.date_end else strdate(a.date_end),
            }
        )
    return JsonResponse({"rows": data})


def load_dreg_detail(request):
    a = DispensaryReg.objects.get(pk=json.loads(request.body)["pk"])
    data = {
        "diagnos": a.diagnos + ' ' + a.illnes,
        "date_start": None if not a.date_start else a.date_start,
        "date_end": None if not a.date_end else a.date_end,
        "close": bool(a.date_end),
        "why_stop": a.why_stop,
        "time_index": a.what_times,
        "identified_index": a.how_identified,
    }
    return JsonResponse(data)


def load_vaccine_detail(request):
    a = VaccineReg.objects.get(pk=json.loads(request.body)["pk"])
    data = {
        "date": a.date,
        "direction": a.direction,
        "title": a.title,
        "series": a.series,
        "amount": a.amount,
        "method": a.method,
        "step": a.step,
        "tap": a.tap,
        "comment": a.comment,
    }
    return JsonResponse(data)


def load_ambulatory_data_detail(request):
    a = AmbulatoryData.objects.get(pk=json.loads(request.body)["pk"])
    str_adate = str(a.date)[0:7]
    data = {
        "date": str_adate,
        "data": a.data,
    }
    return JsonResponse(data)


def load_ambulatory_history(request):
    request_data = json.loads(request.body)
    result = AmbulatoryDataHistory.objects.filter(card__pk=request_data["card_pk"]).order_by('-created_at')
    rows = [{'date': strdate(i.created_at), 'data': i.text} for i in result]

    return JsonResponse({"rows": rows})


def load_benefit_detail(request):
    pk = json.loads(request.body)["card_pk"]
    if pk > -1:
        a = BenefitReg.objects.get(pk=pk)
        data = {
            "benefit_id": a.benefit_id,
            "registration_basis": a.registration_basis,
            "date_start": '' if not a.date_start else a.date_start,
            "date_end": '' if not a.date_end else a.date_end,
            "close": bool(a.date_end),
        }
    else:
        data = {
            "benefit_id": -1,
            "registration_basis": "",
            "date_start": '',
            "date_end": '',
            "close": False,
        }
    return JsonResponse(
        {
            "types": [{"pk": -1, "title": 'Не выбрано'}, *[{"pk": x.pk, "title": str(x)} for x in BenefitType.objects.filter(hide=False).order_by('pk')]],
            **data,
        }
    )


@transaction.atomic
def save_dreg(request):
    rd = json.loads(request.body)
    d = rd["data"]
    pk = rd["pk"]
    n = False
    create_disp_record = False
    if pk == -1:
        a = DispensaryReg.objects.create(card_id=rd["card_pk"])
        pk = a.pk
        n = True
        create_disp_record = True
    else:
        pk = rd["pk"]
        a = DispensaryReg.objects.get(pk=pk)

    Log.log(pk, 40000 if n else 40001, request.user.doctorprofile, rd)

    c = False

    def fd(s):
        if '.' in s:
            s = s.split('.')
            s = '{}-{}-{}'.format(s[2], s[1], s[0])
        return s

    if (
        not a.date_start
        and d["date_start"]
        or str(a.date_start) != fd(d["date_start"])
        or a.spec_reg != request.user.doctorprofile.specialities
        or a.doc_start_reg != request.user.doctorprofile
    ):
        a.date_start = fd(d["date_start"])
        a.doc_start_reg = request.user.doctorprofile
        a.spec_reg = request.user.doctorprofile.specialities
        c = True

    if not a.date_end and d["close"] or (d["close"] and str(a.date_end) != fd(d["date_end"])):
        a.date_end = fd(d["date_end"])
        a.why_stop = d["why_stop"]
        a.doc_end_reg = request.user.doctorprofile
        c = True
    elif d["close"] and a.why_stop != d["why_stop"]:
        a.why_stop = d["why_stop"]
        c = True

    if not d["close"] and (a.date_end or a.why_stop):
        a.date_end = None
        a.why_stop = ''
        a.doc_end_reg = None
        c = True

    i = d["diagnos"].split(' ')
    ds = i.pop(0)
    if len(i) == 0:
        i = ''
    else:
        i = ' '.join(i)

    if a.diagnos != ds or a.illnes != i:
        a.diagnos = ds
        a.illnes = i
        if create_disp_record:
            disp_obj = DispensaryReg.objects.filter(card_id=rd["card_pk"], diagnos=ds, date_start=fd(d["date_start"]), doc_start_reg=request.user.doctorprofile)
            if disp_obj.exists():
                a.delete()
                return JsonResponse({"ok": False, "pk": -1, "c": False})
        c = True

    if d.get('identified_index', 0) != a.how_identified:
        a.how_identified = d.get('identified_index', 0)
        c = True

    if d.get('time_index', 0) != a.what_times:
        a.what_times = d.get('time_index', 0)
        c = True

    if c:
        a.save()

    return JsonResponse({"ok": True, "pk": pk, "c": c})


@transaction.atomic
def save_vaccine(request):
    rd = json.loads(request.body)
    d = rd["data"]
    pk = rd["pk"]
    n = False
    if pk == -1:
        a = VaccineReg.objects.create(card_id=rd["card_pk"])
        pk = a.pk
        n = True
    else:
        pk = rd["pk"]
        a = VaccineReg.objects.get(pk=pk)

    Log.log(pk, 70000 if n else 70001, request.user.doctorprofile, rd)

    c = False

    def fd(s):
        if '.' in s:
            s = s.split('.')
            s = '{}-{}-{}'.format(s[2], s[1], s[0])
        return s

    if str(a.date) != fd(d["date"]):
        a.date = fd(d["date"])
        c = True

    if a.direction != d["direction"]:
        a.direction = d["direction"]
        c = True

    if a.title != d["title"]:
        a.title = d["title"]
        c = True

    if a.series != d["series"]:
        a.series = d["series"]
        c = True

    if a.amount != d["amount"]:
        a.amount = d["amount"]
        c = True

    if a.step != d["step"]:
        a.step = d["step"]
        c = True

    if a.tap != d["tap"]:
        a.tap = d["tap"]
        c = True

    if a.comment != d["comment"]:
        a.comment = d["comment"]
        c = True

    if a.method != d["method"]:
        a.method = d["method"]
        c = True

    if not a.doc:
        a.doc = request.user.doctorprofile
        c = True

    if c:
        a.save()

    return JsonResponse({"ok": True, "pk": pk, "c": c})


@transaction.atomic
def save_ambulatory_data(request):
    rd = json.loads(request.body)
    d = rd["data"]
    pk = rd["pk"]
    date_request = f"{d['date']}-01"
    if pk == -1:
        a = AmbulatoryData.objects.create(card_id=rd["card_pk"])
        pk = a.pk
    else:
        pk = rd["pk"]
        a = AmbulatoryData.objects.get(pk=pk)

    c = False

    def fd(s):
        if '.' in s:
            s = s.split('.')
            s = '{}-{}-{}'.format(s[2], s[1], s[0])
        return s

    if str(a.date) != fd(date_request):
        a.date = fd(date_request)
        c = True

    if a.data != d["data"]:
        a.data = d["data"]
        c = True

    if not a.doc:
        a.doc = request.user.doctorprofile
        c = True

    if c:
        a.save()
        AmbulatoryDataHistory.save_ambulatory_history(rd["card_pk"], request.user.doctorprofile)

    return JsonResponse({"ok": True, "pk": pk, "c": c})


@transaction.atomic
def save_benefit(request):
    rd = json.loads(request.body)
    d = rd["data"]
    pk = rd["pk"]
    n = False

    c = False

    if pk == -1:
        a = BenefitReg.objects.create(card_id=rd["card_pk"], benefit_id=d["benefit_id"])
        pk = a.pk
        n = True
    else:
        pk = rd["pk"]
        a = BenefitReg.objects.get(pk=pk)
        if a.benefit_id != d["benefit_id"]:
            a.benefit_id = d["benefit_id"]
            c = True

    Log.log(pk, 50000 if n else 50001, request.user.doctorprofile, {**rd, "data": {**{k: v for k, v in rd["data"].items() if k not in ['types']}}})

    def fd(s):
        if '.' in s:
            s = s.split('.')
            s = '{}-{}-{}'.format(s[2], s[1], s[0])
        return s

    if not a.date_start and d["date_start"] or str(a.date_start) != fd(d["date_start"]) or a.doc_start_reg != request.user.doctorprofile:
        a.date_start = fd(d["date_start"])
        a.doc_start_reg = request.user.doctorprofile
        c = True

    if a.registration_basis != d["registration_basis"]:
        a.registration_basis = d["registration_basis"]
        c = True

    if not a.date_end and d["close"] or (d["close"] and a.doc_end_reg != request.user.doctorprofile) or (d["close"] and str(a.date_end) != fd(d["date_end"])):
        a.date_end = fd(d["date_end"])
        a.doc_end_reg = request.user.doctorprofile
        c = True

    if not d["close"] and a.date_end:
        a.date_end = None
        a.doc_end_reg = None
        c = True

    if c:
        a.save()

    return JsonResponse({"ok": True, "pk": pk, "c": c})


def load_anamnesis(request):
    request_data = json.loads(request.body)
    card = Card.objects.get(pk=request_data["card_pk"])
    history = []
    for a in AnamnesisHistory.objects.filter(card=card).order_by('-pk') if not request_data.get('skipHistory') else []:
        history.append(
            {
                "pk": a.pk,
                "text": a.text,
                "who_save": {
                    "fio": a.who_save.get_fio(dots=True),
                    "department": a.who_save.podrazdeleniye.get_title(),
                },
                "datetime": a.created_at.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime("%d.%m.%Y %X"),
            }
        )
    data = {
        "text": card.anamnesis_of_life,
        "history": history,
    }
    if request_data.get('withPatient'):
        data['patient'] = card.get_fio_w_card()

    return JsonResponse(data)


def save_anamnesis(request):
    request_data = json.loads(request.body)
    card = Card.objects.get(pk=request_data["card_pk"])
    if card.anamnesis_of_life != request_data["text"]:
        card.anamnesis_of_life = request_data["text"]
        card.save()
        AnamnesisHistory(card=card, text=request_data["text"], who_save=request.user.doctorprofile).save()
    return JsonResponse({"ok": True})


def create_l2_individual_from_card(request):
    request_data = json.loads(request.body)
    polis = request_data['polis']

    has_tfoms_data = False
    if SettingManager.l2('tfoms'):
        from_tfoms = match_enp(polis)

        if from_tfoms:
            has_tfoms_data = True
            Individual.import_from_tfoms(from_tfoms, no_update=True)

    if not has_tfoms_data:
        Individual.import_from_tfoms(
            {
                "enp": polis,
                "family": request_data['family'],
                "given": request_data['name'],
                "patronymic": request_data['patronymic'],
                "gender": request_data['sex'],
                "birthdate": request_data['bdate'],
            },
            no_update=True,
        )

    return JsonResponse({"ok": True})


def is_l2_card(request):
    request_data = json.loads(request.body)
    card = Card.objects.filter(number=request_data['number'], base__internal_type=True).first()
    if card:
        return JsonResponse({"ok": True, "individual_fio": card.individual.fio()})
    else:
        return JsonResponse({"ok": False})
