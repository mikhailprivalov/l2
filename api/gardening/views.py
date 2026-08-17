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
            return JsonResponse(
                {"ok": False, "message": "Признак «Не контролировать поступления» уже установлен у другого вида платежа"}
            )

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

    rate = (
        GardeningPaymentTypeRate.objects.select_related("payment_type")
        .filter(pk=pk, payment_type__hide=False)
        .first()
    )
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
        }
    phones = [
        {"id": phone.pk, "phone": phone.phone or ""}
        for phone in IndividualPhones.objects.filter(individual=individual).order_by("pk")
    ]
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
    }


def _list_owners(real_estate: RealEstate):
    owners = (
        OwnersRealEstate.objects.select_related("individual")
        .filter(real_estate=real_estate, hide=False)
        .order_by("date_start", "pk")
    )
    return [_serialize_owner(owner) for owner in owners]


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

    return JsonResponse({"ok": True, "result": _list_owners(real_estate)})


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

    owner_id = body.get("owner_id")
    owner = None
    if owner_id:
        owner = (
            OwnersRealEstate.objects.select_related("individual")
            .filter(pk=owner_id, real_estate=real_estate, hide=False)
            .first()
        )
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
        owner.save(update_fields=["individual", "date_start", "date_end"])
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
        )

    _sync_individual_phones(individual, body.get("phones"))

    return JsonResponse({"ok": True, "result": _list_owners(real_estate)})


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

    return JsonResponse({"ok": True, "result": _list_owners(real_estate)})


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
        children = (
            item.parent_pay_receipt.filter(hide=False)
            .select_related("payment_type")
            .order_by("date", "pk")
        )
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
    qs = (
        GardeningBankReceipt.objects.select_related("payment_type")
        .filter(real_estate=real_estate, hide=False, parent__isnull=True, date__year=year)
        .order_by("date", "pk")
    )
    return [_serialize_bank_receipt(item, with_children=True) for item in qs]


def _resolve_parent(body, real_estate: RealEstate):
    parent_id = body.get("parent_id") or body.get("parent")
    if not parent_id:
        return None, None
    parent = (
        GardeningBankReceipt.objects.select_related("payment_type")
        .filter(pk=parent_id, hide=False, real_estate=real_estate, parent__isnull=True)
        .first()
    )
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

    item = (
        GardeningBankReceipt.objects.select_related("real_estate", "payment_type", "parent", "parent__payment_type")
        .filter(pk=pk, hide=False)
        .first()
    )
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
            return JsonResponse(
                {"ok": False, "message": "Нельзя сменить вид платежа: есть подчинённые поступления"}
            )

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

    item = (
        GardeningBankReceipt.objects.select_related("real_estate")
        .filter(pk=pk, hide=False)
        .first()
    )
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
    ).aggregate(total=Sum("amount"))["total"]
    return total if total is not None else Decimal("0")


def _receipts_sum_all(payment_type_id, year):
    total = GardeningBankReceipt.objects.filter(
        hide=False,
        payment_type_id=payment_type_id,
        date__year=year,
    ).aggregate(total=Sum("amount"))["total"]
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
    qs = (
        GardeningPaymentType.objects.filter(hide=False, pk__in=ids)
        .prefetch_related("rates")
        .order_by("sort_weight", "pk")
    )
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
