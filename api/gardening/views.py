import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

import simplejson as json
from django.conf import settings as django_settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.db.utils import IntegrityError
from django.http import JsonResponse

from clients.models import Individual, IndividualPhones
from directory.models import (
    GardeningBankReceipt,
    GardeningElectricityMeter,
    GardeningElectricityMeterReading,
    GardeningPaymentType,
    GardeningPaymentTypeRate,
    OwnersRealEstate,
    RealEstate,
)
from laboratory.decorators import group_required


def _parse_date(value, field_name):
    if not value:
        return None, f"Укажите {field_name}"
    if isinstance(value, str):
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date(), None
        except ValueError:
            return None, f"Некорректная {field_name}"
    return None, f"Некорректная {field_name}"


def _parse_optional_date(value, field_name):
    if value in (None, ""):
        return None, None
    return _parse_date(value, field_name)


def _rates_overlap(payment_type_id, date_start, date_end, exclude_id=None):
    qs = GardeningPaymentTypeRate.objects.filter(
        payment_type_id=payment_type_id,
        date_start__isnull=False,
        date_end__isnull=False,
    ).exclude(Q(date_end__lt=date_start) | Q(date_start__gt=date_end))
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    return qs.exists()


def _parse_rate_fields(body):
    date_start, error = _parse_date(body.get("date_start"), "дату начала")
    if error:
        return None, error

    date_end, error = _parse_date(body.get("date_end"), "дату окончания")
    if error:
        return None, error

    if date_start > date_end:
        return None, "Дата начала не может быть позже даты окончания"

    amount_raw = body.get("amount")
    if amount_raw is None or amount_raw == "":
        return None, "Укажите тариф"

    try:
        amount = Decimal(str(amount_raw).replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        return None, "Тариф должен быть числом"

    if amount < 0:
        return None, "Тариф не может быть отрицательным"

    return {"date_start": date_start, "date_end": date_end, "amount": amount}, None


def _serialize_payment_type_by_id(payment_type_id):
    payment_type = GardeningPaymentType.objects.filter(pk=payment_type_id).prefetch_related("rates").first()
    return _serialize_payment_type(payment_type)


def _serialize_payment_type(item: GardeningPaymentType):
    rates = [
        {
            "id": rate.pk,
            "date_start": rate.date_start.isoformat() if rate.date_start else None,
            "date_end": rate.date_end.isoformat() if rate.date_end else None,
            "amount": str(rate.amount),
        }
        for rate in item.rates.all().order_by("date_start", "pk")
    ]
    return {
        "id": item.pk,
        "title": item.title,
        "is_absolute": item.is_absolute,
        "is_by_area": item.is_by_area,
        "is_use_kilowatt": item.is_use_kilowatt,
        "period": item.period,
        "payment_date": item.payment_date.isoformat() if item.payment_date else None,
        "payment_day": item.payment_day,
        "not_control": item.not_control,
        "rates": rates,
    }


def _parse_payment_type_create_body(body):
    title = (body.get("title") or "").strip()
    if not title:
        return None, "Укажите название"

    return {
        "title": title,
        "is_absolute": False,
        "is_by_area": False,
        "is_use_kilowatt": False,
        "period": None,
        "payment_date": None,
        "payment_day": None,
        "not_control": False,
    }, None


def _parse_payment_type_body(body):
    title = (body.get("title") or "").strip()
    if not title:
        return None, "Укажите название"

    is_absolute = bool(body.get("is_absolute"))
    is_by_area = bool(body.get("is_by_area"))
    is_use_kilowatt = bool(body.get("is_use_kilowatt"))
    selected_modes = sum([is_absolute, is_by_area, is_use_kilowatt])
    if selected_modes != 1:
        return None, "Укажите один режим расчёта"

    period = body.get("period")
    if period not in (GardeningPaymentType.PERIOD_YEAR, GardeningPaymentType.PERIOD_MONTH):
        return None, "Укажите период учета"

    payment_date = None
    payment_day = None

    if period == GardeningPaymentType.PERIOD_MONTH:
        payment_day_raw = body.get("payment_day")
        if payment_day_raw is None or payment_day_raw == "":
            return None, "Укажите день оплаты"
        try:
            payment_day = int(payment_day_raw)
        except (TypeError, ValueError):
            return None, "День оплаты должен быть числом"
        if payment_day < 1 or payment_day > 31:
            return None, "День оплаты должен быть от 1 до 31"
    else:
        payment_date, error = _parse_date(body.get("payment_date"), "дату оплаты")
        if error:
            return None, error

    return {
        "title": title,
        "is_absolute": is_absolute,
        "is_by_area": is_by_area,
        "is_use_kilowatt": is_use_kilowatt,
        "period": period,
        "payment_date": payment_date,
        "payment_day": payment_day,
        "not_control": bool(body.get("not_control")),
    }, None


@login_required
@group_required("Бухгалтер садоводства")
def get_real_estates(request):
    result = [{"id": item.pk, "num_object": item.num_object} for item in RealEstate.objects.filter(hide=False).order_by("num_object")]
    return JsonResponse(
        {
            "result": result,
            "year_min": getattr(django_settings, "GARDENING_YEAR_MIN", 2000),
            "year_max_offset": getattr(django_settings, "GARDENING_YEAR_MAX_OFFSET", 2),
        }
    )


@login_required
@group_required("Бухгалтер садоводства")
def create_real_estate(request):
    body = json.loads(request.body)
    num_object = body.get("num_object")

    if num_object is None or num_object == "":
        return JsonResponse({"ok": False, "message": "Укажите номер объекта"})

    try:
        num_object = int(num_object)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "message": "Номер объекта должен быть числом"})

    if num_object <= 0:
        return JsonResponse({"ok": False, "message": "Номер объекта должен быть больше 0"})

    if RealEstate.objects.filter(num_object=num_object).exists():
        return JsonResponse({"ok": False, "message": "Объект с таким номером уже существует"})

    try:
        obj = RealEstate.objects.create(title=str(num_object), num_object=num_object)
    except IntegrityError:
        return JsonResponse({"ok": False, "message": "Объект с таким номером уже существует"})

    return JsonResponse({"ok": True, "result": {"id": obj.pk, "num_object": obj.num_object}})


@login_required
@group_required("Бухгалтер садоводства")
def update_real_estate(request):
    body = json.loads(request.body)
    real_estate_id = body.get("id")
    num_object = body.get("num_object")

    if not real_estate_id:
        return JsonResponse({"ok": False, "message": "Не указан объект"})

    if num_object is None or num_object == "":
        return JsonResponse({"ok": False, "message": "Укажите номер объекта"})

    try:
        num_object = int(num_object)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "message": "Номер объекта должен быть числом"})

    if num_object <= 0:
        return JsonResponse({"ok": False, "message": "Номер объекта должен быть больше 0"})

    obj = RealEstate.objects.filter(pk=real_estate_id, hide=False).first()
    if not obj:
        return JsonResponse({"ok": False, "message": "Объект не найден"})

    if RealEstate.objects.filter(num_object=num_object).exclude(pk=obj.pk).exists():
        return JsonResponse({"ok": False, "message": "Объект с таким номером уже существует"})

    try:
        obj.num_object = num_object
        obj.title = str(num_object)
        obj.save(update_fields=["num_object", "title"])
    except IntegrityError:
        return JsonResponse({"ok": False, "message": "Объект с таким номером уже существует"})

    return JsonResponse({"ok": True, "result": {"id": obj.pk, "num_object": obj.num_object}})


@login_required
@group_required("Бухгалтер садоводства")
def get_payment_types(request):
    result = [_serialize_payment_type(item) for item in GardeningPaymentType.objects.filter(hide=False).prefetch_related("rates").order_by("sort_weight", "pk")]
    return JsonResponse({"result": result})


@login_required
@group_required("Бухгалтер садоводства")
def get_year_payment_types(request):
    if request.method == "POST" and request.body:
        body = json.loads(request.body)
        year = body.get("year")
    else:
        year = request.GET.get("year")

    if not year:
        return JsonResponse({"ok": False, "message": "Не указан год"})

    try:
        year = int(year)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "message": "Некорректный год"})

    return JsonResponse({"ok": True, "result": _payment_types_for_year(year)})


@login_required
@group_required("Бухгалтер садоводства")
def create_payment_type(request):
    body = json.loads(request.body)
    data, error = _parse_payment_type_create_body(body)
    if error:
        return JsonResponse({"ok": False, "message": error})

    obj = GardeningPaymentType.objects.create(**data)
    return JsonResponse({"ok": True, "result": _serialize_payment_type(obj)})


@login_required
@group_required("Бухгалтер садоводства")
def update_payment_type(request):
    body = json.loads(request.body)
    pk = body.get("id")
    if not pk:
        return JsonResponse({"ok": False, "message": "Не указан идентификатор"})

    obj = GardeningPaymentType.objects.filter(pk=pk, hide=False).prefetch_related("rates").first()
    if not obj:
        return JsonResponse({"ok": False, "message": "Вид платежа не найден"})

    data, error = _parse_payment_type_body(body)
    if error:
        return JsonResponse({"ok": False, "message": error})

    if data["not_control"]:
        exists_other = GardeningPaymentType.objects.filter(hide=False, not_control=True).exclude(pk=obj.pk).exists()
        if exists_other:
            return JsonResponse({"ok": False, "message": "Признак «Не контролировать поступления» уже установлен у другого вида платежа"})

    for key, value in data.items():
        setattr(obj, key, value)
    obj.save()
    return JsonResponse({"ok": True, "result": _serialize_payment_type(obj)})


@login_required
@group_required("Бухгалтер садоводства")
def create_payment_type_rate(request):
    body = json.loads(request.body)
    payment_type_id = body.get("payment_type_id")
    if not payment_type_id:
        return JsonResponse({"ok": False, "message": "Не указан вид платежа"})

    payment_type = GardeningPaymentType.objects.filter(pk=payment_type_id, hide=False).first()
    if not payment_type:
        return JsonResponse({"ok": False, "message": "Вид платежа не найден"})

    data, error = _parse_rate_fields(body)
    if error:
        return JsonResponse({"ok": False, "message": error})

    if _rates_overlap(payment_type.pk, data["date_start"], data["date_end"]):
        return JsonResponse({"ok": False, "message": "Период пересекается с другим тарифом этого вида платежа"})

    GardeningPaymentTypeRate.objects.create(payment_type=payment_type, **data)
    return JsonResponse({"ok": True, "result": _serialize_payment_type_by_id(payment_type.pk)})


@login_required
@group_required("Бухгалтер садоводства")
def update_payment_type_rate(request):
    body = json.loads(request.body)
    pk = body.get("id")
    if not pk:
        return JsonResponse({"ok": False, "message": "Не указан идентификатор тарифа"})

    rate = GardeningPaymentTypeRate.objects.select_related("payment_type").filter(pk=pk, payment_type__hide=False).first()
    if not rate:
        return JsonResponse({"ok": False, "message": "Тариф не найден"})

    data, error = _parse_rate_fields(body)
    if error:
        return JsonResponse({"ok": False, "message": error})

    if _rates_overlap(rate.payment_type_id, data["date_start"], data["date_end"], exclude_id=rate.pk):
        return JsonResponse({"ok": False, "message": "Период пересекается с другим тарифом этого вида платежа"})

    for key, value in data.items():
        setattr(rate, key, value)
    rate.save()
    return JsonResponse({"ok": True, "result": _serialize_payment_type_by_id(rate.payment_type_id)})


@login_required
@group_required("Бухгалтер садоводства")
def delete_payment_type_rate(request):
    body = json.loads(request.body)
    pk = body.get("id")
    if not pk:
        return JsonResponse({"ok": False, "message": "Не указан идентификатор тарифа"})

    rate = GardeningPaymentTypeRate.objects.select_related("payment_type").filter(pk=pk, payment_type__hide=False).first()
    if not rate:
        return JsonResponse({"ok": False, "message": "Тариф не найден"})

    payment_type_id = rate.payment_type_id
    rate.delete()
    return JsonResponse({"ok": True, "result": _serialize_payment_type_by_id(payment_type_id)})


def _serialize_owner(owner: OwnersRealEstate):
    individual = owner.individual
    if not individual:
        return {
            "owner_id": owner.pk,
            "individual_id": None,
            "family": "",
            "name": "",
            "patronymic": "",
            "birthday": None,
            "date_start": owner.date_start.isoformat() if owner.date_start else None,
            "date_end": owner.date_end.isoformat() if owner.date_end else None,
            "phones": [],
            "comment": owner.comment or "",
        }
    phones = [{"id": phone.pk, "phone": phone.phone or ""} for phone in IndividualPhones.objects.filter(individual=individual).order_by("pk")]
    return {
        "owner_id": owner.pk,
        "individual_id": individual.pk,
        "family": individual.family or "",
        "name": individual.name or "",
        "patronymic": individual.patronymic or "",
        "birthday": individual.birthday.isoformat() if individual.birthday else None,
        "date_start": owner.date_start.isoformat() if owner.date_start else None,
        "date_end": owner.date_end.isoformat() if owner.date_end else None,
        "phones": phones,
        "comment": owner.comment or "",
    }


def _list_owners(real_estate: RealEstate):
    owners = OwnersRealEstate.objects.select_related("individual").filter(real_estate=real_estate, hide=False).order_by("date_start", "pk")
    return [_serialize_owner(owner) for owner in owners]


def _list_plot_meters(real_estate: RealEstate):
    return [_serialize_plot_meter(item) for item in GardeningElectricityMeter.objects.filter(real_estate=real_estate, hide=False).order_by("sort_weight", "pk")]


def _serialize_plot_meter(meter: GardeningElectricityMeter):
    return {
        "id": meter.pk,
        "title": meter.title,
        "date_start": meter.date_start.isoformat() if meter.date_start else None,
        "date_end": meter.date_end.isoformat() if meter.date_end else None,
    }


def _meter_active_in_month(meter: GardeningElectricityMeter, year, month):
    month_start = date(int(year), int(month), 1)
    month_end = date(int(year), int(month), calendar.monthrange(int(year), int(month))[1])
    if meter.date_start and meter.date_start > month_end:
        return False
    if meter.date_end and meter.date_end < month_start:
        return False
    return True


def _parse_meter_dates(item):
    if not isinstance(item, dict):
        return None, None, None
    date_start, error = _parse_optional_date(item.get("date_start"), "дату начала установки")
    if error:
        return None, None, error
    date_end, error = _parse_optional_date(item.get("date_end"), "дату окончания")
    if error:
        return None, None, error
    if date_start and date_end and date_end < date_start:
        return None, None, "Дата окончания не может быть раньше даты начала установки"
    return date_start, date_end, None


def _owner_payload(real_estate: RealEstate):
    _ensure_meters(real_estate)
    return {
        "owners": _list_owners(real_estate),
        "meters": _list_plot_meters(real_estate),
    }


def _sync_plot_meters(real_estate: RealEstate, meters_raw):
    if not isinstance(meters_raw, list):
        return None
    sort_weight = 0
    for item in meters_raw:
        pk = None
        if isinstance(item, dict):
            title = (item.get("title") or "").strip()
            pk = item.get("id")
        else:
            title = str(item or "").strip()
        if not title:
            continue
        date_start, date_end, error = _parse_meter_dates(item if isinstance(item, dict) else {})
        if error:
            return error
        sort_weight += 1
        meter = None
        if pk:
            meter = GardeningElectricityMeter.objects.filter(pk=pk, real_estate=real_estate, hide=False).first()
        if meter:
            meter.title = title
            meter.date_start = date_start
            meter.date_end = date_end
            meter.sort_weight = sort_weight
            meter.save(update_fields=["title", "date_start", "date_end", "sort_weight"])
        else:
            GardeningElectricityMeter.objects.create(
                real_estate=real_estate,
                title=title,
                date_start=date_start,
                date_end=date_end,
                sort_weight=sort_weight,
            )
    return None


def _close_open_owners(real_estate: RealEstate, date_start, exclude_id=None):
    if not date_start:
        return None
    qs = OwnersRealEstate.objects.filter(real_estate=real_estate, hide=False, date_end__isnull=True)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    close_date = date_start - timedelta(days=1)
    for prev in qs:
        if prev.date_start and close_date < prev.date_start:
            return "Дата начала нового периода пересекается с текущим владельцем"
        prev.date_end = close_date
        prev.save(update_fields=["date_end"])
    return None


def _sync_individual_phones(individual: Individual, phones_raw):
    phones = []
    if isinstance(phones_raw, list):
        for item in phones_raw:
            if isinstance(item, dict):
                value = (item.get("phone") or "").strip()
            else:
                value = str(item or "").strip()
            if value:
                phones.append(value)

    existing = list(IndividualPhones.objects.filter(individual=individual).order_by("pk"))
    for index, phone_value in enumerate(phones):
        if index < len(existing):
            row = existing[index]
            if row.phone != phone_value:
                row.phone = phone_value
                row.save(update_fields=["phone"])
        else:
            IndividualPhones.objects.create(individual=individual, phone=phone_value)

    for row in existing[len(phones) :]:
        row.delete()


@login_required
@group_required("Бухгалтер садоводства")
def get_real_estate_owner(request):
    if request.method == "POST" and request.body:
        body = json.loads(request.body)
        real_estate_id = body.get("real_estate_id") or body.get("id")
    else:
        real_estate_id = request.GET.get("real_estate_id") or request.GET.get("id")
    if not real_estate_id:
        return JsonResponse({"ok": False, "message": "Не указан объект"})

    real_estate = RealEstate.objects.filter(pk=real_estate_id, hide=False).first()
    if not real_estate:
        return JsonResponse({"ok": False, "message": "Объект не найден"})

    return JsonResponse({"ok": True, "result": _owner_payload(real_estate)})


@login_required
@group_required("Бухгалтер садоводства")
def save_real_estate_owner(request):
    body = json.loads(request.body)
    real_estate_id = body.get("real_estate_id")
    if not real_estate_id:
        return JsonResponse({"ok": False, "message": "Не указан объект"})

    real_estate = RealEstate.objects.filter(pk=real_estate_id, hide=False).first()
    if not real_estate:
        return JsonResponse({"ok": False, "message": "Объект не найден"})

    comment = (body.get("comment") or "").strip()

    family = (body.get("family") or "").strip()
    name = (body.get("name") or "").strip()
    patronymic = (body.get("patronymic") or "").strip()
    birthday, error = _parse_date(body.get("birthday"), "дату рождения")
    if error:
        return JsonResponse({"ok": False, "message": error})

    date_start, error = _parse_date(body.get("date_start"), "дату начала")
    if error:
        return JsonResponse({"ok": False, "message": error})

    date_end, error = _parse_optional_date(body.get("date_end"), "дату окончания")
    if error:
        return JsonResponse({"ok": False, "message": error})

    if date_end and date_start > date_end:
        return JsonResponse({"ok": False, "message": "Дата начала не может быть позже даты окончания"})

    if not family and not name and not patronymic:
        return JsonResponse({"ok": False, "message": "Укажите ФИО"})

    meters_raw = body.get("meters")
    if isinstance(meters_raw, list):
        for item in meters_raw:
            if not isinstance(item, dict):
                continue
            if not (item.get("title") or "").strip():
                continue
            _, _, dates_error = _parse_meter_dates(item)
            if dates_error:
                return JsonResponse({"ok": False, "message": dates_error})

    owner_id = body.get("owner_id")
    owner = None
    if owner_id:
        owner = OwnersRealEstate.objects.select_related("individual").filter(pk=owner_id, real_estate=real_estate, hide=False).first()
        if not owner:
            return JsonResponse({"ok": False, "message": "Запись владельца не найдена"})

    if owner:
        if owner.individual_id:
            individual = owner.individual
            individual.family = family
            individual.name = name
            individual.patronymic = patronymic
            individual.birthday = birthday
            individual.save(update_fields=["family", "name", "patronymic", "birthday"])
        else:
            individual = Individual.objects.create(
                family=family,
                name=name,
                patronymic=patronymic,
                birthday=birthday,
            )
            owner.individual = individual
        owner.date_start = date_start
        owner.date_end = date_end
        owner.comment = comment
        owner.save(update_fields=["individual", "date_start", "date_end", "comment"])
    else:
        close_error = _close_open_owners(real_estate, date_start)
        if close_error:
            return JsonResponse({"ok": False, "message": close_error})

        individual = Individual.objects.create(
            family=family,
            name=name,
            patronymic=patronymic,
            birthday=birthday,
        )
        owner = OwnersRealEstate.objects.create(
            real_estate=real_estate,
            individual=individual,
            date_start=date_start,
            date_end=date_end,
            comment=comment,
        )

    _sync_individual_phones(individual, body.get("phones"))
    sync_error = _sync_plot_meters(real_estate, body.get("meters"))
    if sync_error:
        return JsonResponse({"ok": False, "message": sync_error})

    return JsonResponse({"ok": True, "result": _owner_payload(real_estate)})


@login_required
@group_required("Бухгалтер садоводства")
def delete_real_estate_owner(request):
    body = json.loads(request.body)
    owner_id = body.get("owner_id") or body.get("id")
    if not owner_id:
        return JsonResponse({"ok": False, "message": "Не указан владелец"})

    owner = OwnersRealEstate.objects.select_related("real_estate").filter(pk=owner_id, hide=False).first()
    if not owner:
        return JsonResponse({"ok": False, "message": "Запись владельца не найдена"})

    real_estate = owner.real_estate
    if real_estate.hide:
        return JsonResponse({"ok": False, "message": "Объект не найден"})

    owner.hide = True
    owner.save(update_fields=["hide"])

    return JsonResponse({"ok": True, "result": _owner_payload(real_estate)})


def _serialize_bank_receipt(item: GardeningBankReceipt, with_children=False):
    not_control = bool(item.payment_type.not_control) if item.payment_type_id else False
    data = {
        "id": item.pk,
        "real_estate_id": item.real_estate_id,
        "payment_type_id": item.payment_type_id,
        "payment_type_title": item.payment_type.title if item.payment_type_id else "",
        "date": item.date.isoformat() if item.date else None,
        "amount": str(item.amount),
        "comment": item.comment or "",
        "parent_id": item.parent_id,
        "not_control": not_control,
    }
    if with_children:
        children = item.parent_pay_receipt.filter(hide=False).select_related("payment_type").order_by("date", "pk")
        data["parent_pay_receipt"] = [_serialize_bank_receipt(child) for child in children]
    return data


def _payment_types_for_year(year, exclude_not_control=False):
    year_start = f"{int(year)}-01-01"
    year_end = f"{int(year)}-12-31"
    options = []
    seen = set()
    for item in GardeningPaymentType.objects.filter(hide=False).prefetch_related("rates").order_by("sort_weight", "pk"):
        if exclude_not_control and item.not_control:
            continue
        include = item.not_control
        if not include:
            for rate in item.rates.all():
                if not rate.date_start or not rate.date_end:
                    continue
                if rate.date_start.isoformat() <= year_end and rate.date_end.isoformat() >= year_start:
                    include = True
                    break
        if include and item.pk not in seen:
            seen.add(item.pk)
            options.append({"id": item.pk, "label": item.title, "not_control": item.not_control})
    return options


def _bank_receipts_result(real_estate: RealEstate, year):
    return {
        "receipts": _list_bank_receipts(real_estate, year),
        "payment_types": _payment_types_for_year(year),
        "payment_types_alloc": _payment_types_for_year(year, exclude_not_control=True),
    }


def _list_bank_receipts(real_estate: RealEstate, year):
    year = int(year)
    qs = GardeningBankReceipt.objects.select_related("payment_type").filter(real_estate=real_estate, hide=False, parent__isnull=True, date__year=year).order_by("date", "pk")
    return [_serialize_bank_receipt(item, with_children=True) for item in qs]


def _resolve_parent(body, real_estate: RealEstate):
    parent_id = body.get("parent_id") or body.get("parent")
    if not parent_id:
        return None, None
    parent = GardeningBankReceipt.objects.select_related("payment_type").filter(pk=parent_id, hide=False, real_estate=real_estate, parent__isnull=True).first()
    if not parent:
        return None, "Родительский приход не найден"
    if not parent.payment_type_id or not parent.payment_type.not_control:
        return None, "Распределение доступно только для прихода с признаком «Не контролировать поступления»"
    return parent, None


def _check_allocation_amount(parent: GardeningBankReceipt, amount, exclude_id=None):
    qs = parent.parent_pay_receipt.filter(hide=False)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    children_total = sum((child.amount for child in qs), Decimal("0"))
    if children_total + amount > parent.amount:
        return "Сумма распределений превышает сумму прихода"
    return None


def _check_parent_amount_vs_children(parent: GardeningBankReceipt, amount):
    children_total = sum(
        (child.amount for child in parent.parent_pay_receipt.filter(hide=False)),
        Decimal("0"),
    )
    if amount < children_total:
        return "Сумма прихода меньше суммы распределений"
    return None


def _parse_bank_receipt_fields(body, *, for_child=False):
    date_value, error = _parse_date(body.get("date"), "дату")
    if error:
        return None, error

    payment_type_id = body.get("payment_type_id") or body.get("payment_type")
    if not payment_type_id:
        return None, "Укажите вид платежа"

    payment_type = GardeningPaymentType.objects.filter(pk=payment_type_id, hide=False).first()
    if not payment_type:
        return None, "Вид платежа не найден"

    if for_child and payment_type.not_control:
        return None, "Для распределения нельзя выбрать вид платежа «Не контролировать поступления»"

    amount_raw = body.get("amount")
    if amount_raw is None or amount_raw == "":
        return None, "Укажите сумму"

    try:
        amount = Decimal(str(amount_raw).replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        return None, "Сумма должна быть числом"

    if amount < 0:
        return None, "Сумма не может быть отрицательной"

    comment = (body.get("comment") or "").strip()
    if len(comment) > 512:
        return None, "Комментарий слишком длинный"

    return {
        "date": date_value,
        "payment_type": payment_type,
        "amount": amount,
        "comment": comment,
    }, None


@login_required
@group_required("Бухгалтер садоводства")
def get_bank_receipts(request):
    if request.method == "POST" and request.body:
        body = json.loads(request.body)
        real_estate_id = body.get("real_estate_id") or body.get("id")
        year = body.get("year")
    else:
        real_estate_id = request.GET.get("real_estate_id") or request.GET.get("id")
        year = request.GET.get("year")

    if not real_estate_id:
        return JsonResponse({"ok": False, "message": "Не указан объект"})
    if not year:
        return JsonResponse({"ok": False, "message": "Не указан год"})

    real_estate = RealEstate.objects.filter(pk=real_estate_id, hide=False).first()
    if not real_estate:
        return JsonResponse({"ok": False, "message": "Объект не найден"})

    try:
        year = int(year)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "message": "Некорректный год"})

    return JsonResponse({"ok": True, "result": _bank_receipts_result(real_estate, year)})


@login_required
@group_required("Бухгалтер садоводства")
def create_bank_receipt(request):
    body = json.loads(request.body)
    real_estate_id = body.get("real_estate_id")
    if not real_estate_id:
        return JsonResponse({"ok": False, "message": "Не указан объект"})

    real_estate = RealEstate.objects.filter(pk=real_estate_id, hide=False).first()
    if not real_estate:
        return JsonResponse({"ok": False, "message": "Объект не найден"})

    parent, error = _resolve_parent(body, real_estate)
    if error:
        return JsonResponse({"ok": False, "message": error})

    data, error = _parse_bank_receipt_fields(body, for_child=bool(parent))
    if error:
        return JsonResponse({"ok": False, "message": error})

    if parent:
        error = _check_allocation_amount(parent, data["amount"])
        if error:
            return JsonResponse({"ok": False, "message": error})

    year = body.get("year") or data["date"].year
    try:
        year = int(year)
    except (TypeError, ValueError):
        year = data["date"].year

    item = GardeningBankReceipt.objects.create(
        real_estate=real_estate,
        payment_type=data["payment_type"],
        date=data["date"],
        amount=data["amount"],
        comment=data["comment"],
        parent=parent,
    )
    result = _bank_receipts_result(real_estate, year)
    result["item"] = _serialize_bank_receipt(item, with_children=False)
    return JsonResponse({"ok": True, "result": result})


@login_required
@group_required("Бухгалтер садоводства")
def update_bank_receipt(request):
    body = json.loads(request.body)
    pk = body.get("id")
    if not pk:
        return JsonResponse({"ok": False, "message": "Не указан идентификатор"})

    item = GardeningBankReceipt.objects.select_related("real_estate", "payment_type", "parent", "parent__payment_type").filter(pk=pk, hide=False).first()
    if not item:
        return JsonResponse({"ok": False, "message": "Приход не найден"})
    if item.real_estate.hide:
        return JsonResponse({"ok": False, "message": "Объект не найден"})

    data, error = _parse_bank_receipt_fields(body, for_child=bool(item.parent_id))
    if error:
        return JsonResponse({"ok": False, "message": error})

    if item.parent_id is None and not data["payment_type"].not_control:
        has_children = item.parent_pay_receipt.filter(hide=False).exists()
        if has_children:
            return JsonResponse({"ok": False, "message": "Нельзя сменить вид платежа: есть подчинённые поступления"})

    if item.parent_id:
        error = _check_allocation_amount(item.parent, data["amount"], exclude_id=item.pk)
        if error:
            return JsonResponse({"ok": False, "message": error})
    else:
        error = _check_parent_amount_vs_children(item, data["amount"])
        if error:
            return JsonResponse({"ok": False, "message": error})

    item.payment_type = data["payment_type"]
    item.date = data["date"]
    item.amount = data["amount"]
    item.comment = data["comment"]
    item.save(update_fields=["payment_type", "date", "amount", "comment"])

    year = body.get("year") or data["date"].year
    try:
        year = int(year)
    except (TypeError, ValueError):
        year = data["date"].year

    result = _bank_receipts_result(item.real_estate, year)
    result["item"] = _serialize_bank_receipt(item, with_children=bool(item.parent_id is None))
    return JsonResponse({"ok": True, "result": result})


@login_required
@group_required("Бухгалтер садоводства")
def delete_bank_receipt(request):
    body = json.loads(request.body)
    pk = body.get("id")
    if not pk:
        return JsonResponse({"ok": False, "message": "Не указан идентификатор"})

    item = GardeningBankReceipt.objects.select_related("real_estate").filter(pk=pk, hide=False).first()
    if not item:
        return JsonResponse({"ok": False, "message": "Приход не найден"})
    if item.real_estate.hide:
        return JsonResponse({"ok": False, "message": "Объект не найден"})

    year = body.get("year")
    if year:
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = item.date.year if item.date else None
    else:
        year = item.date.year if item.date else None

    real_estate = item.real_estate
    if item.parent_id is None:
        item.parent_pay_receipt.filter(hide=False).update(hide=True)
    item.hide = True
    item.save(update_fields=["hide"])

    if not year:
        return JsonResponse({"ok": True, "result": {"receipts": [], "payment_types": [], "payment_types_alloc": []}})

    return JsonResponse({"ok": True, "result": _bank_receipts_result(real_estate, year)})


def _is_electricity_payment_type(payment_type: GardeningPaymentType):
    title = (payment_type.title or "").strip().lower()
    return bool(payment_type.is_use_kilowatt) or "электроэнергия" in title


def _year_bounds(year):
    return date(int(year), 1, 1), date(int(year), 12, 31)


def _tariff_for_year(payment_type: GardeningPaymentType, year):
    year_start, year_end = _year_bounds(year)
    for rate in payment_type.rates.all():
        if not rate.date_start or not rate.date_end:
            continue
        if rate.date_start <= year_end and rate.date_end >= year_start:
            return rate.amount
    return Decimal("0")


def _receipts_sum(real_estate_id, payment_type_id, year):
    total = GardeningBankReceipt.objects.filter(
        hide=False,
        real_estate_id=real_estate_id,
        payment_type_id=payment_type_id,
        date__year=year,
    ).aggregate(
        total=Sum("amount")
    )["total"]
    return total if total is not None else Decimal("0")


def _receipts_sum_all(payment_type_id, year):
    total = GardeningBankReceipt.objects.filter(
        hide=False,
        payment_type_id=payment_type_id,
        date__year=year,
    ).aggregate(
        total=Sum("amount")
    )["total"]
    return total if total is not None else Decimal("0")


def _balance_before_year(real_estate_id, payment_type: GardeningPaymentType, year):
    if not payment_type.is_absolute:
        return Decimal("0")
    balance = Decimal("0")
    earliest = year - 40
    for y in range(earliest, year):
        receipt = _receipts_sum(real_estate_id, payment_type.pk, y)
        tariff = _tariff_for_year(payment_type, y)
        balance = receipt + balance - tariff
    return balance


def _accounting_payment_types(year, payment_type_id=None):
    options = _payment_types_for_year(year)
    ids = [item["id"] for item in options]
    qs = GardeningPaymentType.objects.filter(hide=False, pk__in=ids).prefetch_related("rates").order_by("sort_weight", "pk")
    result = []
    for item in qs:
        if _is_electricity_payment_type(item):
            continue
        if payment_type_id is not None and item.pk != int(payment_type_id):
            continue
        result.append(item)
    return result


def _format_money(value):
    return f"{Decimal(value).quantize(Decimal('0.01'))}"


@login_required
@group_required("Бухгалтер садоводства")
def get_accounting_summary(request):
    if request.method == "POST" and request.body:
        body = json.loads(request.body)
        year = body.get("year")
        payment_type_id = body.get("payment_type_id")
    else:
        year = request.GET.get("year")
        payment_type_id = request.GET.get("payment_type_id")

    if not year:
        return JsonResponse({"ok": False, "message": "Не указан год"})
    try:
        year = int(year)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "message": "Некорректный год"})

    if payment_type_id in ("", None):
        payment_type_id = None
    else:
        try:
            payment_type_id = int(payment_type_id)
        except (TypeError, ValueError):
            return JsonResponse({"ok": False, "message": "Некорректный вид платежа"})

    date_start, date_end = _year_bounds(year)
    payment_types = _accounting_payment_types(year, payment_type_id)

    if payment_type_id is None:
        items = []
        for payment_type in payment_types:
            items.append(
                {
                    "payment_type_id": payment_type.pk,
                    "title": payment_type.title,
                    "is_absolute": payment_type.is_absolute,
                    "date_start": date_start.isoformat(),
                    "date_end": date_end.isoformat(),
                    "receipts_total": _format_money(_receipts_sum_all(payment_type.pk, year)),
                }
            )
        return JsonResponse({"ok": True, "result": {"mode": "totals", "year": year, "items": items}})

    if not payment_types:
        return JsonResponse(
            {
                "ok": True,
                "result": {
                    "mode": "table",
                    "year": year,
                    "payment_type": None,
                    "rows": [],
                },
            }
        )

    payment_type = payment_types[0]
    estates = RealEstate.objects.filter(hide=False).order_by("num_object")
    tariff = _tariff_for_year(payment_type, year)
    rows = []
    for estate in estates:
        receipt = _receipts_sum(estate.pk, payment_type.pk, year)
        balance = _balance_before_year(estate.pk, payment_type, year)
        if payment_type.is_absolute:
            total = receipt + balance - tariff
            total_str = _format_money(total)
        else:
            total_str = None
        rows.append(
            {
                "real_estate_id": estate.pk,
                "num_object": estate.num_object,
                "receipt": _format_money(receipt),
                "balance": _format_money(balance),
                "tariff": _format_money(tariff),
                "total": total_str,
            }
        )

    return JsonResponse(
        {
            "ok": True,
            "result": {
                "mode": "table",
                "year": year,
                "payment_type": {
                    "payment_type_id": payment_type.pk,
                    "title": payment_type.title,
                    "is_absolute": payment_type.is_absolute,
                    "date_start": date_start.isoformat(),
                    "date_end": date_end.isoformat(),
                    "receipts_total": _format_money(_receipts_sum_all(payment_type.pk, year)),
                },
                "rows": rows,
            },
        }
    )


ELECTRICITY_MONTH_LABELS = (
    "",
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
)


def _electricity_payment_type():
    for item in GardeningPaymentType.objects.filter(hide=False).prefetch_related("rates").order_by("sort_weight", "pk"):
        if _is_electricity_payment_type(item):
            return item
    return None


def _tariff_for_month(payment_type: GardeningPaymentType, year, month):
    if payment_type is None:
        return None
    month_start = date(int(year), int(month), 1)
    last_day = calendar.monthrange(int(year), int(month))[1]
    month_end = date(int(year), int(month), last_day)
    found = None
    found_start = None
    for rate in payment_type.rates.all():
        if not rate.date_start or not rate.date_end:
            continue
        if rate.date_start <= month_end and rate.date_end >= month_start:
            if found is None or rate.date_start > found_start:
                found = rate.amount
                found_start = rate.date_start
    return found


def _receipts_by_month(real_estate_id, payment_type_id):
    totals = {}
    if not payment_type_id:
        return totals
    for item in GardeningBankReceipt.objects.filter(hide=False, real_estate_id=real_estate_id, payment_type_id=payment_type_id, date__isnull=False).only("date", "amount"):
        key = (item.date.year, item.date.month)
        totals[key] = totals.get(key, Decimal("0")) + item.amount
    return totals


def _parse_reading(raw):
    if raw is None or raw == "":
        return None, "Укажите показание"
    try:
        value = Decimal(str(raw).replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        return None, "Показание должно быть числом"
    if value < 0:
        return None, "Показание не может быть отрицательным"
    return value, None


def _parse_month(raw):
    if raw is None or raw == "":
        return None, "Укажите месяц"
    try:
        month = int(raw)
    except (TypeError, ValueError):
        return None, "Месяц должен быть числом"
    if month < 1 or month > 12:
        return None, "Месяц должен быть от 1 до 12"
    return month, None


def _meters_qs(real_estate: RealEstate):
    return GardeningElectricityMeter.objects.filter(real_estate=real_estate, hide=False).order_by("sort_weight", "pk")


def _ensure_meters(real_estate: RealEstate):
    meters = list(_meters_qs(real_estate))
    if meters:
        return meters
    return [GardeningElectricityMeter.objects.create(real_estate=real_estate, title="Счётчик 1", sort_weight=0)]


def _resolve_meter(real_estate: RealEstate, meter_id):
    if not meter_id:
        return None, "Не указан счётчик"
    meter = _meters_qs(real_estate).filter(pk=meter_id).first()
    if not meter:
        return None, "Счётчик не найден"
    return meter, None


def _serialize_electricity_row(curr_row, year, month, calc, plot_calc, show_money):
    row = {
        "id": curr_row.pk if curr_row else None,
        "year": year,
        "month": month,
        "month_label": ELECTRICITY_MONTH_LABELS[month],
        "previous_reading": _format_money(calc["previous_reading"]) if calc["previous_reading"] is not None else None,
        "previous_manual": bool(calc["previous_manual"]),
        "current_reading": _format_money(calc["current_reading"]) if calc["current_reading"] is not None else None,
        "consumption": _format_money(calc["consumption"]) if calc["consumption"] is not None else None,
        "tariff": _format_money(calc["tariff"]) if calc["tariff"] is not None else None,
        "charge": _format_money(calc["charge"]) if calc["charge"] is not None else None,
        "written_off": None,
        "debt": None,
        "receipt": None,
        "remainder": None,
    }
    if show_money:
        row["written_off"] = _format_money(plot_calc["written_off"]) if plot_calc["written_off"] is not None else None
        row["debt"] = _format_money(plot_calc["debt"]) if plot_calc["debt"] is not None else None
        row["receipt"] = _format_money(plot_calc["receipt"])
        row["remainder"] = _format_money(plot_calc["remainder"]) if plot_calc["remainder"] is not None else None
    return row


def _electricity_result(real_estate: RealEstate, year):
    year = int(year)
    meters = _ensure_meters(real_estate)
    payment_type = _electricity_payment_type()
    payment_type_id = payment_type.pk if payment_type else None
    readings_qs = GardeningElectricityMeterReading.objects.filter(hide=False, real_estate=real_estate, meter__hide=False)
    readings = {(item.meter_id, item.year, item.month): item for item in readings_qs}
    receipts_totals = _receipts_by_month(real_estate.pk, payment_type_id)
    start_years = [year]
    if readings:
        start_years.append(min(item[1] for item in readings.keys()))
    if receipts_totals:
        start_years.append(min(item[0] for item in receipts_totals.keys()))
    start_year = min(start_years)
    meter_calc = {}
    plot_calc = {}
    balance = Decimal("0")
    for y in range(start_year, year + 1):
        for month in range(1, 13):
            prev_year, prev_month = (y - 1, 12) if month == 1 else (y, month - 1)
            total_charge = Decimal("0")
            any_charge = False
            for meter in meters:
                if not _meter_active_in_month(meter, y, month):
                    meter_calc[(meter.pk, y, month)] = {
                        "previous_reading": None,
                        "previous_manual": False,
                        "current_reading": None,
                        "consumption": None,
                        "tariff": None,
                        "charge": None,
                    }
                    continue
                prev_row = readings.get((meter.pk, prev_year, prev_month))
                curr_row = readings.get((meter.pk, y, month))
                auto_prev = prev_row.reading if prev_row else None
                manual_prev = curr_row.previous_reading_manual if curr_row else None
                prev_reading = manual_prev if manual_prev is not None else auto_prev
                curr_reading = curr_row.reading if curr_row else None
                previous_manual = curr_row is not None and curr_row.previous_reading_manual is not None
                consumption = None
                if prev_reading is not None and curr_reading is not None:
                    consumption = curr_reading - prev_reading
                tariff = _tariff_for_month(payment_type, y, month) if payment_type else None
                charge = None
                if consumption is not None and tariff is not None:
                    charge = consumption * tariff
                    any_charge = True
                    total_charge += charge
                meter_calc[(meter.pk, y, month)] = {
                    "previous_reading": prev_reading,
                    "previous_manual": previous_manual,
                    "current_reading": curr_reading,
                    "consumption": consumption,
                    "tariff": tariff,
                    "charge": charge,
                }
            receipts = receipts_totals.get((y, month), Decimal("0"))
            available = balance + receipts
            written_off = None
            debt = None
            if any_charge:
                written_off = min(available, total_charge)
                if written_off < 0:
                    written_off = Decimal("0")
                debt = total_charge - written_off
                remainder = available - written_off
            else:
                remainder = available
            balance = remainder
            plot_calc[(y, month)] = {
                "receipt": receipts,
                "written_off": written_off,
                "debt": debt,
                "remainder": remainder,
            }

    first_money_by_month = {}
    for month in range(1, 13):
        for meter in meters:
            if _meter_active_in_month(meter, year, month):
                first_money_by_month[month] = meter.pk
                break

    meters_payload = []
    for meter in meters:
        rows = []
        for month in range(1, 13):
            if not _meter_active_in_month(meter, year, month):
                continue
            curr_row = readings.get((meter.pk, year, month))
            show_money = first_money_by_month.get(month) == meter.pk
            rows.append(
                _serialize_electricity_row(
                    curr_row,
                    year,
                    month,
                    meter_calc[(meter.pk, year, month)],
                    plot_calc[(year, month)],
                    show_money,
                )
            )
        if not rows:
            continue
        payload = _serialize_plot_meter(meter)
        payload["show_money"] = first_money_by_month.get(1) == meter.pk
        payload["rows"] = rows
        meters_payload.append(payload)

    tariffs = {}
    for month in range(1, 13):
        tariff_value = meter_calc.get((meters[0].pk, year, month), {}).get("tariff") if meters else None
        tariffs[str(month)] = _format_money(tariff_value) if tariff_value is not None else None
    first_rows = meters_payload[0]["rows"] if meters_payload else []
    return {
        "payment_type": {"id": payment_type.pk, "title": payment_type.title} if payment_type else None,
        "tariffs": tariffs,
        "meters": meters_payload,
        "rows": first_rows,
    }


def _resolve_real_estate_year(body=None, get=None):
    source = body if body is not None else {}
    get = get or {}
    real_estate_id = source.get("real_estate_id") or source.get("id") or get.get("real_estate_id") or get.get("id")
    year = source.get("year") or get.get("year")
    if not real_estate_id:
        return None, None, JsonResponse({"ok": False, "message": "Не указан объект"})
    if not year:
        return None, None, JsonResponse({"ok": False, "message": "Не указан год"})
    try:
        year = int(year)
    except (TypeError, ValueError):
        return None, None, JsonResponse({"ok": False, "message": "Некорректный год"})
    real_estate = RealEstate.objects.filter(pk=real_estate_id, hide=False).first()
    if not real_estate:
        return None, None, JsonResponse({"ok": False, "message": "Объект не найден"})
    return real_estate, year, None


@login_required
@group_required("Бухгалтер садоводства")
def get_electricity_readings(request):
    if request.method == "POST" and request.body:
        body = json.loads(request.body)
        real_estate, year, error = _resolve_real_estate_year(body=body)
    else:
        real_estate, year, error = _resolve_real_estate_year(get=request.GET)
    if error:
        return error
    return JsonResponse({"ok": True, "result": _electricity_result(real_estate, year)})


@login_required
@group_required("Бухгалтер садоводства")
def create_electricity_reading(request):
    body = json.loads(request.body)
    real_estate, year, error = _resolve_real_estate_year(body=body)
    if error:
        return error

    month, error = _parse_month(body.get("month"))
    if error:
        return JsonResponse({"ok": False, "message": error})

    reading, error = _parse_reading(body.get("reading") if "reading" in body else body.get("current_reading"))
    if error:
        return JsonResponse({"ok": False, "message": error})

    previous_reading_manual = None
    if "previous_reading" in body:
        previous_raw = body.get("previous_reading")
        if previous_raw not in (None, ""):
            previous_reading_manual, error = _parse_reading(previous_raw)
            if error:
                return JsonResponse({"ok": False, "message": error})

    meter, meter_error = _resolve_meter(real_estate, body.get("meter_id"))
    if meter_error:
        return JsonResponse({"ok": False, "message": meter_error})

    existing = GardeningElectricityMeterReading.objects.filter(real_estate=real_estate, meter=meter, year=year, month=month, hide=False).first()
    if existing:
        return JsonResponse({"ok": False, "message": "Показание за этот месяц уже есть"})

    hidden = GardeningElectricityMeterReading.objects.filter(real_estate=real_estate, meter=meter, year=year, month=month, hide=True).first()
    if hidden:
        hidden.hide = False
        hidden.reading = reading
        hidden.previous_reading_manual = previous_reading_manual
        hidden.save(update_fields=["hide", "reading", "previous_reading_manual"])
    else:
        GardeningElectricityMeterReading.objects.create(
            real_estate=real_estate,
            meter=meter,
            year=year,
            month=month,
            reading=reading,
            previous_reading_manual=previous_reading_manual,
        )

    return JsonResponse({"ok": True, "result": _electricity_result(real_estate, year)})


@login_required
@group_required("Бухгалтер садоводства")
def update_electricity_reading(request):
    body = json.loads(request.body)
    pk = body.get("id")
    if not pk:
        return JsonResponse({"ok": False, "message": "Не указан идентификатор"})

    item = GardeningElectricityMeterReading.objects.select_related("real_estate").filter(pk=pk, hide=False).first()
    if not item:
        return JsonResponse({"ok": False, "message": "Показание не найдено"})
    if item.real_estate.hide:
        return JsonResponse({"ok": False, "message": "Объект не найден"})

    has_reading = "reading" in body or "current_reading" in body
    has_previous = "previous_reading" in body
    has_month = "month" in body
    if not has_reading and not has_previous and not has_month:
        return JsonResponse({"ok": False, "message": "Не указано показание"})

    update_fields = []
    if has_month:
        month, error = _parse_month(body.get("month"))
        if error:
            return JsonResponse({"ok": False, "message": error})
        if month != item.month:
            exists = (
                GardeningElectricityMeterReading.objects.filter(
                    real_estate=item.real_estate,
                    meter_id=item.meter_id,
                    year=item.year,
                    month=month,
                    hide=False,
                )
                .exclude(pk=item.pk)
                .exists()
            )
            if exists:
                return JsonResponse({"ok": False, "message": "Показание за этот месяц уже есть"})
            item.month = month
            update_fields.append("month")
    if has_reading:
        reading, error = _parse_reading(body.get("reading") if "reading" in body else body.get("current_reading"))
        if error:
            return JsonResponse({"ok": False, "message": error})
        item.reading = reading
        update_fields.append("reading")

    if has_previous:
        previous_raw = body.get("previous_reading")
        if previous_raw in (None, ""):
            item.previous_reading_manual = None
        else:
            previous_reading, error = _parse_reading(previous_raw)
            if error:
                return JsonResponse({"ok": False, "message": error})
            item.previous_reading_manual = previous_reading
        update_fields.append("previous_reading_manual")

    item.save(update_fields=update_fields)

    year = body.get("year") or item.year
    try:
        year = int(year)
    except (TypeError, ValueError):
        year = item.year

    return JsonResponse({"ok": True, "result": _electricity_result(item.real_estate, year)})


@login_required
@group_required("Бухгалтер садоводства")
def delete_electricity_reading(request):
    body = json.loads(request.body)
    pk = body.get("id")
    if not pk:
        return JsonResponse({"ok": False, "message": "Не указан идентификатор"})

    item = GardeningElectricityMeterReading.objects.select_related("real_estate").filter(pk=pk, hide=False).first()
    if not item:
        return JsonResponse({"ok": False, "message": "Показание не найдено"})
    if item.real_estate.hide:
        return JsonResponse({"ok": False, "message": "Объект не найден"})

    year = body.get("year") or item.year
    try:
        year = int(year)
    except (TypeError, ValueError):
        year = item.year

    real_estate = item.real_estate
    item.hide = True
    item.save(update_fields=["hide"])
    return JsonResponse({"ok": True, "result": _electricity_result(real_estate, year)})


@login_required
@group_required("Бухгалтер садоводства")
def create_electricity_meter(request):
    body = json.loads(request.body)
    real_estate, year, error = _resolve_real_estate_year(body=body)
    if error:
        return error

    meters = list(_meters_qs(real_estate))
    title = (body.get("title") or "").strip() or f"Счётчик {len(meters) + 1}"
    date_start, date_end, dates_error = _parse_meter_dates(body)
    if dates_error:
        return JsonResponse({"ok": False, "message": dates_error})
    sort_weight = (meters[-1].sort_weight if meters else 0) + 1
    GardeningElectricityMeter.objects.create(
        real_estate=real_estate,
        title=title,
        date_start=date_start,
        date_end=date_end,
        sort_weight=sort_weight,
    )
    return JsonResponse({"ok": True, "result": _electricity_result(real_estate, year)})


@login_required
@group_required("Бухгалтер садоводства")
def update_electricity_meter(request):
    body = json.loads(request.body)
    real_estate_id = body.get("real_estate_id")
    if not real_estate_id:
        return JsonResponse({"ok": False, "message": "Не указан объект"})
    real_estate = RealEstate.objects.filter(pk=real_estate_id, hide=False).first()
    if not real_estate:
        return JsonResponse({"ok": False, "message": "Объект не найден"})
    year = body.get("year")
    if year not in (None, ""):
        try:
            year = int(year)
        except (TypeError, ValueError):
            return JsonResponse({"ok": False, "message": "Некорректный год"})
    else:
        year = None
    meter, meter_error = _resolve_meter(real_estate, body.get("id") or body.get("meter_id"))
    if meter_error:
        return JsonResponse({"ok": False, "message": meter_error})
    title = (body.get("title") or "").strip()
    if not title:
        return JsonResponse({"ok": False, "message": "Укажите название счётчика"})
    date_start, date_end, dates_error = _parse_meter_dates(body)
    if dates_error:
        return JsonResponse({"ok": False, "message": dates_error})
    meter.title = title
    meter.date_start = date_start
    meter.date_end = date_end
    meter.save(update_fields=["title", "date_start", "date_end"])
    if year:
        return JsonResponse({"ok": True, "result": _electricity_result(real_estate, year)})
    return JsonResponse({"ok": True, "result": _owner_payload(real_estate)})


@login_required
@group_required("Бухгалтер садоводства")
def delete_electricity_meter(request):
    return JsonResponse({"ok": False, "message": "Счётчик нельзя удалить, укажите дату окончания"})
