from laboratory.decorators import group_required
from django.contrib.auth.decorators import login_required
from django.conf import settings
import simplejson as json
from collections import defaultdict

from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.utils.dateparse import parse_date

from laboratory.settings import ACCOMPANYING_CHILD, CHAMBER_DOCTOR_GROUP_ID, CDA_ID_FOR_DATE_IS_EXTRACT
from laboratory.utils import current_time
from podrazdeleniya.models import Chamber, Bed, PatientToBed, PatientToBedDateComment, PatientStationarWithoutBeds
from directions.models import Issledovaniya, Napravleniya
from slog.models import Log
from utils.response import status_response
import datetime
from .sql_func import (
    load_patient_without_bed_by_department,
    load_attending_doctor_by_department,
    load_attending_doctor_by_department_and_group_title,
    load_patients_stationar_unallocated_sql,
    load_chambers_and_beds_by_department,
    get_closing_protocols,
    load_plan_operations_next_day,
)
from .discharge_sync import (
    _read_discharge_date_from_protocol,
    apply_discharge_dates_to_hosp_record,
    get_discharge_date_for_direction,
    sync_patient_without_bed_discharge_date,
)
from ..stationar.sql_func import get_extract_by_department_for_period
import calendar


def _accompanying_child_from_request(request_data):
    raw = (request_data.get("accompanyng_child_type") or "").strip()
    if not raw:
        return "", "-"
    if raw not in ACCOMPANYING_CHILD:
        return "", "-"
    sex = (ACCOMPANYING_CHILD.get(raw) or "-")[:2]
    return raw[:10], sex


def _patient_fields_from_direction_client(direction_pk: int):
    """ФИО, пол, д.р., возраст из карты направления (Napravleniya.client.individual)."""
    nap = Napravleniya.objects.select_related("client__individual").filter(pk=direction_pk).first()
    if not nap:
        return None
    ind = nap.client.individual
    patient_fio_text = (ind.fio(short=False, full=False, npf=False) or "").strip()[:128]
    patient_sex = (ind.sex or "м").strip()[:2] if (ind.sex or "").strip() else "м"
    birthday = ind.birthday
    patient_age_text = ""
    if birthday:
        today = datetime.date.today()
        years = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
        if years >= 0:
            patient_age_text = str(min(years, 999))[:3]
    return patient_fio_text, patient_sex, birthday, patient_age_text


def _save_ptb_date_comment(patient_to_bed, comment_date, comment_raw):
    """Один комментарий на календарную дату: PatientToBedDateComment с непустым date_comment."""
    if comment_date is None:
        return
    text = (comment_raw or "").strip()[:255]
    PatientToBedDateComment.objects.filter(patient_to_bed=patient_to_bed, date_comment=comment_date).delete()
    if text:
        PatientToBedDateComment.objects.create(
            patient_to_bed=patient_to_bed,
            date_comment=comment_date,
            comment=text,
        )


def _replicate_ptb_comment_to_following_days(patient_to_bed, from_date, comment_raw):
    """Тот же текст комментария на все дни после from_date до конца периода (plan/date_out), включительно."""
    if from_date is None:
        return
    period_end = _hosp_visual_end(patient_to_bed)
    if period_end == _HOSP_OPEN_END:
        return
    text = (comment_raw or "").strip()[:255]
    d = from_date + datetime.timedelta(days=1)
    while d <= period_end:
        _save_ptb_date_comment(patient_to_bed, d, text)
        d += datetime.timedelta(days=1)


_HOSP_OPEN_END = datetime.date(2200, 1, 1)


def _hosp_visual_start(item):
    return item.plan_date_in or item.date_in


def _hosp_uses_plan_calendar(item):
    return item.plan_date_in is not None or item.plan_date_out is not None


def _hosp_visual_end(item):
    """Конец периода на календаре. При плановых датах — plan_date_out, иначе date_out (не min обоих)."""
    if _hosp_uses_plan_calendar(item):
        if item.plan_date_out is not None:
            return item.plan_date_out
        if item.date_out is not None:
            return item.date_out
        return _HOSP_OPEN_END
    if item.date_out is not None:
        return item.date_out
    return _HOSP_OPEN_END


def _hosp_tail_end_date(item):
    end = _hosp_visual_end(item)
    return end if end != _HOSP_OPEN_END else None


def _align_ptb_date_out_with_plan(item):
    """Подтянуть date_out к plan_date_out, чтобы продление плана отображалось на доске."""
    if not _hosp_uses_plan_calendar(item) or item.plan_date_out is None:
        return
    if item.date_out is None or item.date_out < item.plan_date_out:
        item.date_out = item.plan_date_out
    elif item.date_out > item.plan_date_out:
        item.date_out = item.plan_date_out


def _bed_range_has_overlap(bed_id, from_d, to_d, exclude_pk=None):
    """Пересечение с другой записью PatientToBed на этой койке, диапазон [from_d, to_d] включительно; to_d=None — бессрочно."""
    to_eff = to_d if to_d is not None else _HOSP_OPEN_END
    if from_d > to_eff:
        return False
    qs = PatientToBed.objects.filter(bed_id=bed_id)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    for o in qs:
        os_d = _hosp_visual_start(o)
        oe_d = _hosp_visual_end(o)
        if from_d <= oe_d and to_eff >= os_d:
            return True
    return False


def _proposed_hosp_period(plan_date_in, plan_date_out, fallback_date_in=None, fallback_date_out=None):
    from_d = plan_date_in or fallback_date_in or datetime.date.today()
    if plan_date_in is not None or plan_date_out is not None:
        to_d = plan_date_out
    else:
        to_d = fallback_date_out
    return from_d, to_d


def _default_hospitalization_period_days():
    period_days = settings.PERIOD_DAYS_DEFAULT_HOSPITALIZATION
    try:
        period_days = int(period_days)
    except (TypeError, ValueError):
        period_days = 3
    if period_days < 1:
        period_days = 1
    return period_days


def _strip_calendar_dates(
    plan_date_in=None,
    plan_date_out=None,
    date_in=None,
    date_out=None,
    fallback_plan_date_in=None,
):
    """Период черновика: plan_* приоритетнее, выписка из протокола сокращает конец."""
    plan_in = plan_date_in or date_in
    plan_out = plan_date_out or date_out
    if plan_in and not plan_out and fallback_plan_date_in is None:
        plan_out = plan_in + datetime.timedelta(days=_default_hospitalization_period_days() - 1)
    if not plan_in and fallback_plan_date_in:
        plan_in = fallback_plan_date_in
        plan_out = fallback_plan_date_in + datetime.timedelta(days=_default_hospitalization_period_days() - 1)
    return plan_in, plan_out, date_in, date_out


def _direction_hosp_calendar_meta(direction_pk, fallback_plan_date_in=None):
    """Период и признак выписки для черновика / календаря по direction_id."""
    if not direction_pk:
        return {"is_extract": False}
    discharge_date = get_discharge_date_for_direction(direction_pk)
    pswb = PatientStationarWithoutBeds.objects.filter(direction_id=direction_pk).order_by("-pk").first()
    ptb = PatientToBed.objects.filter(direction_id=direction_pk).order_by("-pk").first()
    plan_date_in = None
    plan_date_out = None
    date_in = None
    date_out = None
    is_extract = False
    if pswb:
        plan_date_in = pswb.plan_date_in
        plan_date_out = pswb.plan_date_out
        date_in = pswb.date_in
        date_out = pswb.date_out
        is_extract = bool(pswb.is_extract)
    elif ptb:
        plan_date_in = ptb.plan_date_in
        plan_date_out = ptb.plan_date_out
        date_in = ptb.date_in
        date_out = ptb.date_out
        is_extract = bool(ptb.is_extract)
    plan_date_in, plan_date_out, date_in, date_out = _strip_calendar_dates(
        plan_date_in,
        plan_date_out,
        date_in,
        date_out,
        fallback_plan_date_in=fallback_plan_date_in,
    )
    if discharge_date:
        plan_date_out = discharge_date
        date_out = discharge_date
        plan_in_eff = plan_date_in or date_in
        if plan_in_eff and discharge_date < plan_in_eff:
            plan_date_in = discharge_date
    meta = {"is_extract": is_extract}
    if plan_date_in:
        meta["plan_date_in"] = str(plan_date_in)
    if plan_date_out:
        meta["plan_date_out"] = str(plan_date_out)
    if date_in:
        meta["date_in"] = str(date_in)
    if date_out:
        meta["date_out"] = str(date_out)
    return meta


def _strip_patient_row_from_sql(patient, fallback_plan_date_in=None):
    """Строка API для черновика из SQL + выписка из протокола."""
    direction_id = patient.direction_id
    discharge_date = get_discharge_date_for_direction(direction_id) if direction_id else None
    plan_date_in, plan_date_out, date_in, date_out = _strip_calendar_dates(
        getattr(patient, "plan_date_in", None),
        getattr(patient, "plan_date_out", None),
        getattr(patient, "date_in", None),
        getattr(patient, "date_out", None),
        fallback_plan_date_in=fallback_plan_date_in,
    )
    if discharge_date:
        plan_date_out = discharge_date
        date_out = discharge_date
        plan_in_eff = plan_date_in or date_in
        if plan_in_eff and discharge_date < plan_in_eff:
            plan_date_in = discharge_date
    row = {"is_extract": bool(getattr(patient, "is_extract", False))}
    if plan_date_in:
        row["plan_date_in"] = str(plan_date_in)
    if plan_date_out:
        row["plan_date_out"] = str(plan_date_out)
    if date_in:
        row["date_in"] = str(date_in)
    if date_out:
        row["date_out"] = str(date_out)
    return row


def _calendar_plan_dates(item):
    """Если есть только date_in без date_out и plan_date_out — заполнить plan_date_in/out и сохранить в БД."""
    plan_date_in = item.plan_date_in
    plan_date_out = item.plan_date_out
    if item.date_in and item.date_out is None and item.plan_date_out is None:
        plan_date_in = item.date_in
        plan_date_out = item.date_in + datetime.timedelta(days=_default_hospitalization_period_days() - 1)
        update_fields = []
        if item.plan_date_in != plan_date_in:
            item.plan_date_in = plan_date_in
            update_fields.append("plan_date_in")
        if item.plan_date_out != plan_date_out:
            item.plan_date_out = plan_date_out
            update_fields.append("plan_date_out")
        if update_fields:
            item.save(update_fields=update_fields)
    return plan_date_in, plan_date_out


def _check_bed_period_overlap(bed_id, plan_date_in, plan_date_out, exclude_pk=None, fallback_date_in=None, fallback_date_out=None):
    if plan_date_in and plan_date_out and plan_date_in > plan_date_out:
        return "Дата начала не может быть позже даты окончания"
    from_d, to_d = _proposed_hosp_period(plan_date_in, plan_date_out, fallback_date_in, fallback_date_out)
    if _bed_range_has_overlap(bed_id, from_d, to_d, exclude_pk):
        return "На этой койке период пересекается с другой госпитализацией"
    return None


def _parse_ymd_date(value):
    if not value:
        return None
    parsed = parse_date(value)
    if parsed:
        return parsed
    try:
        return datetime.datetime.strptime(value, "%d.%m.%Y").date()
    except Exception:
        return None


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on", "да")
    return False


def _resolve_direction_id_by_fio(fio_text, department_id):
    fio = " ".join((fio_text or "").split()).strip()
    if not fio:
        return None
    fio_parts = fio.split(" ")
    family = fio_parts[0] if len(fio_parts) > 0 else ""
    name = fio_parts[1] if len(fio_parts) > 1 else ""
    patronymic = fio_parts[2] if len(fio_parts) > 2 else ""
    direction = Napravleniya.objects.filter(cancel=False, hospital_department_override_id=department_id).select_related("client__individual").order_by("-id").first()
    if family:
        direction_qs = Napravleniya.objects.filter(cancel=False, hospital_department_override_id=department_id).select_related("client__individual").order_by("-id")
        direction_qs = direction_qs.filter(client__individual__family__iexact=family)
        if name:
            direction_qs = direction_qs.filter(client__individual__name__iexact=name)
        if patronymic:
            direction_qs = direction_qs.filter(client__individual__patronymic__iexact=patronymic)
        direction = direction_qs.first()
    return direction.pk if direction else None


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def get_unallocated_patients(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    transferable_epicrisis_titles = ('переводной эпикриз', 'Переводной эпикриз', 'ПЕРЕВОДНОЙ ЭПИКРИЗ', 'переводной', 'Переводной', 'ПЕРЕВОДНОЙ')
    all_histories = load_patients_stationar_unallocated_sql(department_pk)
    all_issledovaniya_ids = [history.issledovanie_id for history in all_histories]
    all_issledovaniya_ids = tuple(all_issledovaniya_ids)
    closed_issledovaniya_ids = []
    if all_issledovaniya_ids:
        closed_histories = get_closing_protocols(all_issledovaniya_ids, transferable_epicrisis_titles)
        closed_issledovaniya_ids = [extract.parent_id for extract in closed_histories]
        closed_issledovaniya_ids = set(closed_issledovaniya_ids)

    occupied_direction_ids = set(
        PatientToBed.objects.filter(
            bed__chamber__podrazdelenie_id=department_pk,
            direction_id__isnull=False,
        ).values_list("direction_id", flat=True)
    ) | set(
        PatientStationarWithoutBeds.objects.filter(
            department_id=department_pk,
        ).values_list("direction_id", flat=True)
    )

    patients = [
        {
            "fio": f'{patient.family} {patient.name} {patient.patronymic if patient.patronymic else ""}',
            "age": patient.age,
            "short_fio": f'{patient.family} {patient.name[0]}. {patient.patronymic[0] if patient.patronymic else ""}.',
            "sex": patient.sex,
            "direction_pk": patient.napravleniye_id,
            "service_title": patient.service_title,
        }
        for patient in load_patients_stationar_unallocated_sql(department_pk)
        if patient.issledovanie_id not in closed_issledovaniya_ids
        and patient.napravleniye_id not in occupied_direction_ids
    ]

    return JsonResponse({"data": patients})


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def get_chambers_and_beds(request):
    request_data = json.loads(request.body)
    department_id = request_data.get('department_pk', -1)
    chambers = {}
    current_date = current_time(True)
    next_date = current_date + datetime.timedelta(days=1)
    start_time = f"{next_date.year}-{next_date.month}-{next_date.day} 00:00"
    end_time = f"{next_date.year}-{next_date.month}-{next_date.day} 23:59"
    operation_plan = load_plan_operations_next_day(start_time, end_time)
    directions_ids_operation = [int(operation.direction) for operation in operation_plan]
    chambers_beds = load_chambers_and_beds_by_department(department_id)
    for chamber in chambers_beds:
        if not chambers.get(chamber.chamber_id):
            chambers[chamber.chamber_id] = {
                "pk": chamber.chamber_id,
                "label": chamber.chamber_title,
                "beds": {},
            }
        if not chamber.bed_id:
            continue
        chambers[chamber.chamber_id]["beds"][chamber.bed_id] = {
            "pk": chamber.bed_id,
            "bed_number": chamber.bed_number,
            "doctor": [],
            "patient": [],
        }
        if chamber.direction_id:
            chambers[chamber.chamber_id]["beds"][chamber.bed_id]["patient"].append(
                {
                    "direction_pk": chamber.direction_id,
                    "fio": f"{chamber.patient_family} {chamber.patient_name} {chamber.patient_patronymic if chamber.patient_patronymic else ''}",
                    "short_fio": f"{chamber.patient_family} {chamber.patient_name[0]}. {chamber.patient_patronymic[0] if chamber.patient_patronymic else ''}.",
                    "age": chamber.patient_age,
                    "sex": chamber.patient_sex,
                    "operationNextDay": chamber.direction_id in directions_ids_operation,
                }
            )
        if chamber.doctor_id:
            chambers[chamber.chamber_id]["beds"][chamber.bed_id]["doctor"].append(
                {
                    "pk": chamber.doctor_id,
                    "fio": f"{chamber.doctor_family} {chamber.doctor_name} {chamber.doctor_patronymic if chamber.doctor_patronymic else ''}",
                    "short_fio": f"{chamber.doctor_family} {chamber.doctor_name[0]}. {chamber.doctor_patronymic[0] if chamber.doctor_patronymic else ''}.",
                    "highlight": False,
                }
            )

    result = []
    for chamber in chambers.values():
        chamber["beds"] = [val for val in chamber["beds"].values()]
        result.append(chamber)

    return JsonResponse({"data": result})


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def entrance_patient_to_bed(request):
    request_data = json.loads(request.body)
    bed_id = request_data.get('bed_id')
    direction_id = request_data.get('direction_id')
    doctor_id = request_data.get('doctor_id')
    user = request.user
    bed: Bed = Bed.objects.filter(pk=bed_id).select_related('chamber').first()
    if not bed:
        return status_response(False, "ID кровати обязателен")
    bed_department_id = bed.chamber.podrazdelenie_id
    user_can_edit = Chamber.check_user(user, bed_department_id)
    if not user_can_edit:
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    if not PatientToBed.objects.filter(bed_id=bed_id, date_out=None).exists():
        patient_to_bed = PatientToBed(direction_id=direction_id, bed_id=bed_id, doctor_id=doctor_id)
        patient_to_bed.save()
        Log.log(direction_id, 230000, user.doctorprofile, {"direction_id": direction_id, "bed_id": bed_id, "department_id": bed_department_id, "patient_to_bed": patient_to_bed.pk})
    return status_response(True)


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def extract_patient_bed(request):
    request_data = json.loads(request.body)
    direction_pk = request_data.get('patient')
    user = request.user
    patient: PatientToBed = PatientToBed.objects.filter(direction_id=direction_pk, date_out=None).select_related('bed__chamber').first()
    if not patient:
        return status_response(False, "ID истории болезни обязателен")
    bed_department_id = patient.bed.chamber.podrazdelenie_id
    user_can_edit = Chamber.check_user(user, bed_department_id)
    if not user_can_edit:
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    discharge_date = None
    for extract_iss in (
        Issledovaniya.objects.filter(time_confirmation__isnull=False)
        .filter(Q(napravleniye_id=direction_pk) | Q(napravleniye__parent_id=direction_pk))
        .select_related("research")
        .order_by("-time_confirmation")
    ):
        if extract_iss.research.is_extract_service:
            discharge_date = _read_discharge_date_from_protocol(extract_iss)
            if discharge_date:
                break
    discharge_eff = discharge_date or datetime.date.today()
    apply_discharge_dates_to_hosp_record(patient, discharge_eff)
    sync_patient_without_bed_discharge_date(direction_pk, discharge_eff)
    Log.log(
        direction_pk,
        230001,
        user.doctorprofile,
        {
            "direction_id": direction_pk,
            "bed_id": patient.bed_id,
            "department_id": bed_department_id,
        },
    )
    return status_response(True)


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def get_attending_doctors(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    only_stationar_role = bool(request_data.get('only_stationar_role', False))
    if only_stationar_role:
        attending_doctors = load_attending_doctor_by_department_and_group_title(department_pk, 'Врач стационара')
        doctors = [
            {
                "pk": doctor.id,
                "fio": f'{doctor.family} {doctor.name} {doctor.patronymic if doctor.patronymic else ""}',
                "short_fio": f'{doctor.family} {doctor.name[0]}. {doctor.patronymic[0] if doctor.patronymic else ""}.',
                "highlight": False,
            }
            for doctor in attending_doctors
        ]
        result = {"ok": True, "message": "", "data": doctors}
    elif CHAMBER_DOCTOR_GROUP_ID:
        group_id = CHAMBER_DOCTOR_GROUP_ID
        attending_doctors = load_attending_doctor_by_department(department_pk, group_id)
        doctors = [
            {
                "pk": doctor.id,
                "fio": f'{doctor.family} {doctor.name} {doctor.patronymic if doctor.patronymic else ""}',
                "short_fio": f'{doctor.family} {doctor.name[0]}. {doctor.patronymic[0] if doctor.patronymic else ""}.',
                "highlight": False,
            }
            for doctor in attending_doctors
        ]
        result = {"ok": True, "message": "", "data": doctors}
    else:
        result = {"ok": False, "message": "Группа прав для врачей не настроена", "data": []}
    return JsonResponse(result)


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def update_doctor_to_bed(request):
    request_data = json.loads(request.body)
    user = request.user
    doctor_obj = request_data.get('doctor')
    doctor_id = doctor_obj.get('doctor_pk')
    direction_id = doctor_obj.get('direction_id')
    is_assign = doctor_obj.get('is_assign')
    patient_to_bed = PatientToBed.objects.filter(direction_id=direction_id, date_out=None).select_related('bed__chamber').first()
    bed_department_id = patient_to_bed.bed.chamber.podrazdelenie_id
    user_can_edit = Chamber.check_user(user, bed_department_id)
    if not user_can_edit:
        result = {"ok": False, "message": "Пользователь не принадлежит к данному подразделению"}
        return result
    result = PatientToBed.update_doctor(doctor_id, patient_to_bed, is_assign)
    if result:
        if is_assign:
            type_log = 230002
        else:
            type_log = 230003
        Log.log(
            direction_id,
            type_log,
            user.doctorprofile,
            {
                "direction_id": direction_id,
                "bed_id": patient_to_bed.bed_id,
                "department_id": bed_department_id,
                "doctor_id": doctor_id,
            },
        )
    return JsonResponse({"ok": result, "message": ""})


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def get_patients_without_bed(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk', -1)
    patient_to_bed = load_patient_without_bed_by_department(department_pk)

    patients = []
    for patient in patient_to_bed:
        row = {
            "fio": f"{patient.patient_family} {patient.patient_name} {patient.patient_patronymic if patient.patient_patronymic else ''}",
            "short_fio": f"{patient.patient_family} {patient.patient_name[0]}. {patient.patient_patronymic[0] if patient.patient_patronymic else ''}.",
            "age": patient.patient_age,
            "sex": patient.patient_sex,
            "direction_pk": patient.direction_id,
            "doctor_pk": patient.doctor_id,
        }
        row.update(_strip_patient_row_from_sql(patient, datetime.date.today()))
        patients.append(row)
    return JsonResponse({"data": patients})


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def get_directions_hosp_meta(request):
    request_data = json.loads(request.body)
    direction_pks = request_data.get("direction_pks") or []
    items = []
    for raw in direction_pks:
        try:
            pk = int(raw)
        except (TypeError, ValueError):
            continue
        if pk <= 0:
            continue
        meta = _direction_hosp_calendar_meta(pk, datetime.date.today())
        meta["direction_pk"] = pk
        items.append(meta)
    return JsonResponse({"ok": True, "data": items})


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def save_patient_without_bed(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk')
    patient_obj = request_data.get('patient_obj') or {}
    doctor_id = request_data.get('doctor_id')
    direction_pk = patient_obj.get("direction_pk")
    if not direction_pk:
        return status_response(False, "Направление обязательно")
    user = request.user
    user_can_edit = Chamber.check_user(user, department_pk)
    if not user_can_edit:
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    plan_date_in = _parse_ymd_date(request_data.get("plan_date_in") or patient_obj.get("plan_date_in"))
    plan_date_out = _parse_ymd_date(request_data.get("plan_date_out") or patient_obj.get("plan_date_out"))
    date_out = _parse_ymd_date(request_data.get("date_out") or patient_obj.get("date_out"))
    is_extract = _parse_bool(request_data.get("is_extract"))
    if patient_obj.get("is_extract") is not None:
        is_extract = _parse_bool(patient_obj.get("is_extract"))
    existing_pswb = PatientStationarWithoutBeds.objects.filter(
        direction_id=direction_pk,
        department_id=department_pk,
    ).first()
    if existing_pswb:
        is_extract = is_extract or bool(existing_pswb.is_extract)
    today = datetime.date.today()
    if not plan_date_in:
        plan_date_in = today
    if not plan_date_out:
        plan_date_out = plan_date_in + datetime.timedelta(days=_default_hospitalization_period_days() - 1)
    defaults = {
        "department_id": department_pk,
        "doctor_id": doctor_id,
        "plan_date_in": plan_date_in,
        "plan_date_out": plan_date_out,
        "date_out": date_out,
        "is_extract": is_extract,
    }
    patient_without_bed, created = PatientStationarWithoutBeds.objects.get_or_create(
        direction_id=direction_pk,
        defaults=defaults,
    )
    if created and patient_without_bed.department_id != department_pk:
        patient_without_bed.department_id = department_pk
        patient_without_bed.save(update_fields=["department_id"])
    if not created:
        patient_without_bed.doctor_id = doctor_id
        patient_without_bed.plan_date_in = plan_date_in
        patient_without_bed.plan_date_out = plan_date_out
        patient_without_bed.date_out = date_out
        patient_without_bed.is_extract = is_extract or bool(patient_without_bed.is_extract)
        patient_without_bed.save(update_fields=["doctor_id", "plan_date_in", "plan_date_out", "date_out", "is_extract"])
    Log.log(
        patient_obj["direction_pk"],
        230004,
        user.doctorprofile,
        {
            "direction_id": patient_obj["direction_pk"],
            "department_id": department_pk,
            "doctor_id": doctor_id,
        },
    )
    return status_response(True)


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def delete_patient_without_bed(request):
    request_data = json.loads(request.body)
    department_pk = request_data.get('department_pk')
    patient_obj = request_data.get('patient_obj')
    user = request.user
    user_can_edit = Chamber.check_user(user, department_pk)
    if not user_can_edit:
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    patient_without_bed = PatientStationarWithoutBeds.objects.get(direction_id=patient_obj["direction_pk"])
    patient_without_bed.delete()
    Log.log(
        patient_obj["direction_pk"],
        230005,
        user.doctorprofile,
        {
            "direction_id": patient_obj["direction_pk"],
            "department_id": department_pk,
        },
    )
    return status_response(True)


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def get_accompanying_child_options(request):
    options = [{"id": k, "label": f"{k} ({v})"} for k, v in ACCOMPANYING_CHILD.items()]
    return JsonResponse({"ok": True, "message": "", "data": options})


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def get_hospitalization_calendar(request):
    request_data = json.loads(request.body)
    department_id = request_data.get("department_pk", -1)
    doctor_id = request_data.get("doctor_pk")
    start_date = _parse_ymd_date(request_data.get("start_date"))
    end_date = _parse_ymd_date(request_data.get("end_date"))
    if not start_date or not end_date:
        return JsonResponse({"ok": False, "message": "Период обязателен", "data": {"chambers": [], "records": []}})
    chambers_rows = load_chambers_and_beds_by_department(department_id)
    chambers_map = {}
    bed_ids = []
    beds_included = set()
    for row in chambers_rows:
        if not chambers_map.get(row.chamber_id):
            chambers_map[row.chamber_id] = {"pk": row.chamber_id, "label": row.chamber_title, "beds": []}
        if row.bed_id:
            key = (row.chamber_id, row.bed_id)
            if key in beds_included:
                continue
            beds_included.add(key)
            chambers_map[row.chamber_id]["beds"].append({"pk": row.bed_id, "bed_number": row.bed_number})
            bed_ids.append(row.bed_id)
    records = []
    if bed_ids:
        patients_qs = PatientToBed.objects.filter(bed_id__in=bed_ids).select_related("doctor", "direction__client__individual")
        if doctor_id:
            patients_qs = patients_qs.filter(doctor_id=doctor_id)
        items = list(patients_qs)
        for item in items:
            _calendar_plan_dates(item)
        visible_pks = []
        for item in items:
            item_start = _hosp_visual_start(item)
            item_end = _hosp_visual_end(item)
            if item_end < start_date or item_start > end_date:
                continue
            visible_pks.append(item.pk)
        comments_by_ptb = defaultdict(dict)
        if visible_pks:
            for row in PatientToBedDateComment.objects.filter(
                patient_to_bed_id__in=visible_pks,
                date_comment__isnull=False,
                date_comment__gte=start_date,
                date_comment__lte=end_date,
            ):
                comments_by_ptb[row.patient_to_bed_id][str(row.date_comment)] = row.comment or ""
        for item in items:
            item_start = _hosp_visual_start(item)
            item_end = _hosp_visual_end(item)
            if item_end < start_date or item_start > end_date:
                continue
            fio = item.patient_fio_text or ""
            if not fio and item.direction_id:
                fio = item.direction.client.individual.fio()
            date_comments = {}
            for d_str, txt in comments_by_ptb.get(item.pk, {}).items():
                d = parse_date(d_str)
                if d is None:
                    continue
                if item_start <= d <= item_end:
                    date_comments[d_str] = txt
            records.append(
                {
                    "pk": item.pk,
                    "bed_pk": item.bed_id,
                    "doctor_pk": item.doctor_id,
                    "doctor_fio": item.doctor.get_fio() if item.doctor_id else "",
                    "direction_pk": item.direction_id,
                    "patient_fio": fio,
                    "date_in": str(item.date_in) if item.date_in else None,
                    "date_out": str(item.date_out) if item.date_out else None,
                    "plan_date_in": str(item.plan_date_in) if item.plan_date_in else None,
                    "plan_date_out": str(item.plan_date_out) if item.plan_date_out else None,
                    "patient_sex": item.patient_sex,
                    "birthday": str(item.birthday) if item.birthday else None,
                    "patient_age_text": item.patient_age_text,
                    "accompanyng_child_type": item.accompanyng_child_type or "",
                    "accompanyng_child_sex": item.accompanyng_child_sex or "-",
                    "date_comments": date_comments,
                    "is_day_hosp": bool(item.is_day_hosp),
                    "is_need_sick": bool(item.is_need_sick),
                    "is_extract": bool(item.is_extract),
                }
            )
    view_mode = request_data.get("view_mode")
    start_date = request_data.get("start_date")
    end_date = request_data.get("end_date")
    department_pk = request_data.get("department_pk")
    date_start = ''
    date_end = ''
    if view_mode == 'day':
        date_start = f"{start_date} 00:00:00"
        date_end = f"{end_date} 23:59:59"
    elif view_mode == 'week':
        date_start = f"{start_date} 00:00:00"
        date_end = f"{end_date} 23:59:59"
    elif view_mode == 'month':
        month = start_date.split("-")[1]
        year = start_date.split("-")[0]
        month_obj = int(month)
        _, num_days = calendar.monthrange(int(year), month_obj)
        date_start = datetime.date(int(year), month_obj, 1)
        date_end = datetime.date(int(year), month_obj, num_days)
    extract_proto_for_period = get_extract_by_department_for_period(date_start, date_end, CDA_ID_FOR_DATE_IS_EXTRACT, (department_pk,))
    extracts_data = {}
    total_direction_list = []
    for i in extract_proto_for_period:
        if not extracts_data.get(i.date_extract):
            extracts_data[i.date_extract] = {"count": 1, "directionsList": [i.napravleniye_id], "patientExtracts": [f"{i.patient_family} {i.patient_name[0]}.{i.patient_patronymic[0]}"]}
        else:
            extracts_data[i.date_extract]["count"] += 1
            extracts_data[i.date_extract]["patientExtracts"].append(f"{i.patient_family} {i.patient_name[0]}.{i.patient_patronymic[0]}")
        total_direction_list.append(i.napravleniye_id)

    extracts_count = sum(item["count"] for item in extracts_data.values())
    return JsonResponse(
        {
            "ok": True,
            "message": "",
            "data": {
                "chambers": list(chambers_map.values()),
                "records": records,
                "default_period_days": _default_hospitalization_period_days(),
                "extracts": {"count": extracts_count, "directionList": total_direction_list, **extracts_data},
            },
        }
    )


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def save_hospitalization_by_fio(request):
    request_data = json.loads(request.body)
    bed_id = request_data.get("bed_id")
    doctor_id = request_data.get("doctor_id")
    department_id = request_data.get("department_pk")
    patient_fio_text = (request_data.get("patient_fio_text") or "").strip()
    patient_sex = (request_data.get("patient_sex") or "м").strip()[:2]
    birthday = _parse_ymd_date(request_data.get("birthday"))
    patient_age_text = (request_data.get("patient_age_text") or "").strip()[:3]
    direction_id = request_data.get("direction_id")
    plan_date_in = _parse_ymd_date(request_data.get("plan_date_in"))
    plan_date_out = _parse_ymd_date(request_data.get("plan_date_out"))
    is_need_sick = _parse_bool(request_data.get("is_need_sick"))
    comment = (request_data.get("comment") or "").strip()[:255]
    acc_type, acc_sex = _accompanying_child_from_request(request_data)
    user = request.user
    bed = Bed.objects.filter(pk=bed_id).select_related("chamber").first()
    if not bed:
        return status_response(False, "ID кровати обязателен")
    if bed.chamber.podrazdelenie_id != department_id:
        return status_response(False, "Койка не принадлежит подразделению")
    user_can_edit = Chamber.check_user(user, department_id)
    if not user_can_edit:
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    # if not direction_id:
    #     print("department_id", department_id, "--", department_id)
    #     direction_id = _resolve_direction_id_by_fio(patient_fio_text, department_id)
    # if not direction_id:
    #     return status_response(False, "Не найдено направление для указанного ФИО")

    direction_fk = None
    if "direction_id" in request_data and request_data.get("direction_id") not in (None, "", 0, "0"):
        try:
            did = int(request_data.get("direction_id"))
        except (TypeError, ValueError):
            return status_response(False, "Некорректный номер направления")
        if did <= 0 or not Napravleniya.objects.filter(pk=did).exists():
            return status_response(False, "Направление не найдено")
        direction_fk = did
    auto_default_period = bool(request_data.get("auto_default_period"))
    if auto_default_period and plan_date_in and plan_date_out is None:
        plan_date_out = plan_date_in + datetime.timedelta(days=_default_hospitalization_period_days() - 1)
    if bool(request_data.get("fill_patient_from_direction")) and direction_fk:
        filled = _patient_fields_from_direction_client(direction_fk)
        if not filled:
            return status_response(False, "Направление не найдено")
        patient_fio_text, patient_sex, birthday, patient_age_text = filled
    if not patient_fio_text:
        return status_response(False, "Укажите ФИО пациента")
    overlap_err = _check_bed_period_overlap(bed_id, plan_date_in, plan_date_out)
    if overlap_err:
        return status_response(False, overlap_err)
    is_extract = _parse_bool(request_data.get("is_extract"))
    if direction_fk:
        pswb = PatientStationarWithoutBeds.objects.filter(
            direction_id=direction_fk,
            department_id=department_id,
        ).first()
        if pswb:
            is_extract = is_extract or bool(pswb.is_extract)
        ptb = PatientToBed.objects.filter(direction_id=direction_fk).order_by("-pk").first()
        if ptb:
            is_extract = is_extract or bool(ptb.is_extract)
    patient_to_bed = PatientToBed(
        direction_id=direction_fk,
        bed_id=bed_id,
        doctor_id=doctor_id,
        plan_date_in=plan_date_in,
        plan_date_out=plan_date_out,
        patient_fio_text=patient_fio_text,
        patient_sex=patient_sex or "м",
        birthday=birthday,
        patient_age_text=patient_age_text,
        accompanyng_child_type=acc_type,
        accompanyng_child_sex=acc_sex,
        is_need_sick=is_need_sick,
        is_extract=is_extract,
    )
    _align_ptb_date_out_with_plan(patient_to_bed)
    patient_to_bed.save()
    comment_date = _parse_ymd_date(request_data.get("comment_date"))
    if comment_date is None and comment and plan_date_in:
        comment_date = plan_date_in
    if comment_date is not None:
        _save_ptb_date_comment(patient_to_bed, comment_date, comment)
        if bool(request_data.get("comment_replicate_following")):
            _replicate_ptb_comment_to_following_days(patient_to_bed, comment_date, comment)
    Log.log(
        bed_id,
        230000,
        user.doctorprofile,
        {"direction_id": direction_id, "bed_id": bed_id, "department_id": department_id, "patient_to_bed": patient_to_bed.pk},
    )
    return JsonResponse({"ok": True, "message": "", "result": {"pk": patient_to_bed.pk}})


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def update_hospitalization_record(request):
    request_data = json.loads(request.body)
    record_pk = request_data.get("record_pk")
    doctor_id = request_data.get("doctor_id")
    patient_fio_text = (request_data.get("patient_fio_text") or "").strip()
    patient_sex = (request_data.get("patient_sex") or "м").strip()[:2]
    birthday = _parse_ymd_date(request_data.get("birthday"))
    patient_age_text = (request_data.get("patient_age_text") or "").strip()[:3]
    plan_date_in = _parse_ymd_date(request_data.get("plan_date_in"))
    plan_date_out = _parse_ymd_date(request_data.get("plan_date_out"))
    comment = (request_data.get("comment") or "").strip()[:255]
    acc_type, acc_sex = _accompanying_child_from_request(request_data)
    user = request.user
    record = PatientToBed.objects.filter(pk=record_pk).select_related("bed__chamber").first()
    if not record:
        return status_response(False, "Запись не найдена")
    department_id = record.bed.chamber.podrazdelenie_id
    if not Chamber.check_user(user, department_id):
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    overlap_err = _check_bed_period_overlap(
        record.bed_id,
        plan_date_in,
        plan_date_out,
        exclude_pk=record.pk,
        fallback_date_in=record.date_in,
        fallback_date_out=record.date_out,
    )
    if overlap_err:
        return status_response(False, overlap_err)
    if "direction_id" in request_data:
        dir_raw = request_data.get("direction_id")
        if dir_raw in (None, "", 0, "0"):
            record.direction_id = None
        else:
            try:
                did = int(dir_raw)
            except (TypeError, ValueError):
                return status_response(False, "Некорректный номер направления")
            if did <= 0 or not Napravleniya.objects.filter(pk=did).exists():
                return status_response(False, "Направление не найдено")
            record.direction_id = did
    record.doctor_id = doctor_id if doctor_id else None
    record.patient_fio_text = patient_fio_text
    record.patient_sex = patient_sex or "м"
    record.birthday = birthday
    record.patient_age_text = patient_age_text
    record.plan_date_in = plan_date_in
    record.plan_date_out = plan_date_out
    _align_ptb_date_out_with_plan(record)
    record.accompanyng_child_type = acc_type
    record.accompanyng_child_sex = acc_sex
    if "is_need_sick" in request_data:
        record.is_need_sick = _parse_bool(request_data.get("is_need_sick"))
    record.save()
    comment_date = _parse_ymd_date(request_data.get("comment_date"))
    if comment_date is not None:
        _save_ptb_date_comment(record, comment_date, comment)
        if bool(request_data.get("comment_replicate_following")):
            _replicate_ptb_comment_to_following_days(record, comment_date, comment)
    Log.log(
        record.bed_id,
        230006,
        user.doctorprofile,
        {"record_pk": record.pk, "direction_id": record.direction_id, "bed_id": record.bed_id, "department_id": department_id},
    )
    return JsonResponse({"ok": True, "message": "", "result": {"pk": record.pk}})


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def set_hospitalization_day_hosp(request):
    request_data = json.loads(request.body)
    record_pk = request_data.get("record_pk")
    if record_pk is None or "is_day_hosp" not in request_data:
        return status_response(False, "Недостаточно данных")
    try:
        record_pk = int(record_pk)
    except (TypeError, ValueError):
        return status_response(False, "Некорректный идентификатор записи")
    is_day_hosp = bool(request_data.get("is_day_hosp"))
    user = request.user
    record = PatientToBed.objects.filter(pk=record_pk).select_related("bed__chamber").first()
    if not record:
        return status_response(False, "Запись не найдена")
    department_id = record.bed.chamber.podrazdelenie_id
    if not Chamber.check_user(user, department_id):
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    record.is_day_hosp = is_day_hosp
    record.save(update_fields=["is_day_hosp"])
    Log.log(
        record.bed_id,
        230009,
        user.doctorprofile,
        {"record_pk": record.pk, "is_day_hosp": is_day_hosp, "department_id": department_id},
    )
    return JsonResponse({"ok": True, "message": "", "result": {"pk": record.pk, "is_day_hosp": is_day_hosp}})


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def clear_patient_from_bed(request):
    request_data = json.loads(request.body)
    record_pk = request_data.get("record_pk")
    if not record_pk:
        return status_response(False, "Недостаточно данных")
    try:
        record_pk = int(record_pk)
    except (TypeError, ValueError):
        return status_response(False, "Некорректные идентификаторы")
    user = request.user
    record = PatientToBed.objects.filter(pk=record_pk).select_related("bed__chamber").first()
    if not record:
        return status_response(False, "Запись не найдена")
    department_id = record.bed.chamber.podrazdelenie_id
    if not Chamber.check_user(user, department_id):
        return status_response(False, "Пользователь не принадлежит к данному подразделению")
    bed_id_log = record.bed_id
    direction_id_log = record.direction_id
    rec_pk = record.pk
    record.delete()
    Log.log(
        bed_id_log,
        230008,
        user.doctorprofile,
        {"record_pk": rec_pk, "direction_id": direction_id_log, "bed_id": bed_id_log, "department_id": department_id},
    )
    return JsonResponse({"ok": True, "message": "", "result": {"pk": rec_pk}})


@login_required
@group_required("Оператор лечащего врача", "Лечащий врач")
def move_hospitalization_to_bed(request):
    request_data = json.loads(request.body)
    record_pk = request_data.get("record_pk")
    target_bed_id = request_data.get("target_bed_id")
    move_from_date = _parse_ymd_date(request_data.get("move_from_date"))
    department_pk = request_data.get("department_pk")
    if not record_pk or not target_bed_id or not move_from_date or not department_pk:
        return status_response(False, "Недостаточно данных для переноса")
    try:
        record_pk = int(record_pk)
        target_bed_id = int(target_bed_id)
        department_pk = int(department_pk)
    except (TypeError, ValueError):
        return status_response(False, "Некорректные идентификаторы")
    user = request.user
    with transaction.atomic():
        old = PatientToBed.objects.select_for_update().filter(pk=record_pk).select_related("bed__chamber").first()
        if not old:
            return status_response(False, "Запись не найдена")
        src_dept = old.bed.chamber.podrazdelenie_id
        if src_dept != department_pk:
            return status_response(False, "Запись не относится к выбранному подразделению")
        if not Chamber.check_user(user, src_dept):
            return status_response(False, "Пользователь не принадлежит к данному подразделению")
        tgt_bed = Bed.objects.select_related("chamber").filter(pk=target_bed_id).first()
        if not tgt_bed or tgt_bed.chamber.podrazdelenie_id != src_dept:
            return status_response(False, "Целевая койка недоступна")
        if old.bed_id == target_bed_id:
            return status_response(False, "Укажите другую койку")
        vstart = _hosp_visual_start(old)
        vend = _hosp_visual_end(old)
        if move_from_date < vstart or move_from_date > vend:
            return status_response(False, "Дата вне периода текущей госпитализации")
        uses_plan = _hosp_uses_plan_calendar(old)
        tail_plan_out = old.plan_date_out
        tail_date_out = old.date_out
        tail_end = _hosp_tail_end_date(old)
        if _bed_range_has_overlap(target_bed_id, move_from_date, tail_end, None):
            return status_response(False, "На целевой койке уже есть пациент в этот период")
        if move_from_date <= vstart:
            old.bed_id = target_bed_id
            old.save(update_fields=["bed_id"])
            Log.log(
                target_bed_id,
                230007,
                user.doctorprofile,
                {
                    "record_pk": old.pk,
                    "target_bed_id": target_bed_id,
                    "move_from_date": str(move_from_date),
                    "mode": "full_move",
                    "department_id": department_pk,
                },
            )
            return JsonResponse({"ok": True, "message": "", "result": {"pk": old.pk, "split": False}})
        prev_day = move_from_date - datetime.timedelta(days=1)
        if prev_day < vstart:
            return status_response(False, "Некорректная дата разделения")
        if uses_plan:
            old.plan_date_out = prev_day
            old.date_out = prev_day
            old.save(update_fields=["plan_date_out", "date_out"])
        else:
            old.date_out = prev_day
            old.save(update_fields=["date_out"])
        new = PatientToBed(
            bed_id=target_bed_id,
            direction_id=old.direction_id,
            doctor_id=old.doctor_id,
            plan_date_in=move_from_date if uses_plan else None,
            plan_date_out=tail_plan_out if uses_plan else None,
            patient_fio_text=old.patient_fio_text or "",
            patient_sex=old.patient_sex or "м",
            birthday=old.birthday,
            patient_age_text=old.patient_age_text or "",
            accompanyng_child_type=old.accompanyng_child_type or "",
            accompanyng_child_sex=old.accompanyng_child_sex or "-",
            is_need_sick=bool(old.is_need_sick),
            is_extract=bool(old.is_extract),
        )
        if not uses_plan:
            new.date_out = tail_date_out
        new.save()
        PatientToBed.objects.filter(pk=new.pk).update(date_in=move_from_date)
        PatientToBedDateComment.objects.filter(
            patient_to_bed=old,
            date_comment__isnull=False,
            date_comment__gte=move_from_date,
        ).update(patient_to_bed=new)
        PatientToBedDateComment.objects.filter(patient_to_bed=old, date_comment__isnull=True).delete()
        Log.log(
            target_bed_id,
            230007,
            user.doctorprofile,
            {
                "old_record_pk": old.pk,
                "new_record_pk": new.pk,
                "target_bed_id": target_bed_id,
                "move_from_date": str(move_from_date),
                "mode": "split",
                "department_id": department_pk,
            },
        )
        return JsonResponse({"ok": True, "message": "", "result": {"pk": new.pk, "split": True, "old_pk": old.pk}})
