from datetime import datetime
from decimal import Decimal, InvalidOperation

import simplejson as json
from django.conf import settings as django_settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.utils import IntegrityError
from django.http import JsonResponse

from directory.models import GardeningPaymentType, GardeningPaymentTypeRate, RealEstate
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
        for rate in item.rates.all().order_by("-date_start", "pk")
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
    }, None


@login_required
@group_required("Бухгалтер садоводства")
def get_real_estates(request):
    result = [
        {"id": item.pk, "num_object": item.num_object}
        for item in RealEstate.objects.filter(hide=False).order_by("num_object")
    ]
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
def get_payment_types(request):
    result = [
        _serialize_payment_type(item)
        for item in GardeningPaymentType.objects.filter(hide=False).prefetch_related("rates").order_by("sort_weight", "pk")
    ]
    return JsonResponse({"result": result})


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

    rate = (
        GardeningPaymentTypeRate.objects.select_related("payment_type")
        .filter(pk=pk, payment_type__hide=False)
        .first()
    )
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
