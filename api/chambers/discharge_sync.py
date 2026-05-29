"""Синхронизация даты выписки из протокола в PatientToBed."""

import datetime
from typing import Optional

from django.db.models import Q
from django.utils.dateparse import parse_date

from directions.models import Issledovaniya, ParaclinicResult
from external_system.models import CdaFields
from podrazdeleniya.models import PatientToBed, PatientStationarWithoutBeds
from utils.dates import normalize_date

from api.stationar.stationar_func import hosp_get_curent_hosp_dir

CDA_DISCHARGE_DATE_TITLE = "в.э.-Дата выписки"
FALLBACK_DISCHARGE_FIELD_TITLE = "Дата выписки"


def _parse_discharge_date_value(raw: str):
    s = (raw or "").strip()
    if not s:
        return None
    if len(s) >= 10 and s[4] == "-":
        parsed = parse_date(s[:10])
        if parsed:
            return parsed
    normalized = normalize_date(s)
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue
    return parse_date(s)


def _read_discharge_date_from_protocol(iss: Issledovaniya):
    cda = CdaFields.objects.filter(title=CDA_DISCHARGE_DATE_TITLE).first()
    if cda:
        result = ParaclinicResult.objects.filter(issledovaniye=iss, field__cda_option_id=cda.pk).exclude(value="").order_by("field__order").first()
        if result and result.value:
            parsed = _parse_discharge_date_value(result.value)
            if parsed:
                return parsed
    result = ParaclinicResult.objects.filter(issledovaniye=iss, field__title=FALLBACK_DISCHARGE_FIELD_TITLE).exclude(value="").order_by("field__order").first()
    if result and result.value:
        return _parse_discharge_date_value(result.value)
    return None


def get_discharge_date_for_direction(direction_pk):
    """Дата выписки из подтверждённого протокола выписки по направлению."""
    if not direction_pk:
        return None
    for extract_iss in (
        Issledovaniya.objects.filter(time_confirmation__isnull=False)
        .filter(Q(napravleniye_id=direction_pk) | Q(napravleniye__parent_id=direction_pk))
        .select_related("research")
        .order_by("-time_confirmation")
    ):
        if extract_iss.research.is_extract:
            discharge_date = _read_discharge_date_from_protocol(extract_iss)
            if discharge_date:
                return discharge_date
    return None


def _effective_plan_date_in(record) -> Optional[datetime.date]:
    return record.plan_date_in or record.date_in


def apply_discharge_dates_to_hosp_record(record, discharge_date) -> None:
    """PatientToBed или PatientStationarWithoutBeds: конец = выписка; начало не позже выписки."""
    if not discharge_date:
        return
    record.plan_date_out = discharge_date
    record.date_out = discharge_date
    record.is_extract = True
    update_fields = ["plan_date_out", "date_out", "is_extract"]

    if not record.plan_date_in and record.date_in:
        record.plan_date_in = record.date_in
        update_fields.append("plan_date_in")

    plan_in = _effective_plan_date_in(record)
    if plan_in and discharge_date < plan_in:
        record.plan_date_in = discharge_date
        if "plan_date_in" not in update_fields:
            update_fields.append("plan_date_in")

    record.save(update_fields=update_fields)


def _apply_discharge_date_to_without_bed(pswb: PatientStationarWithoutBeds, discharge_date) -> None:
    apply_discharge_dates_to_hosp_record(pswb, discharge_date)


def sync_patient_without_bed_discharge_date(direction_pk, discharge_date) -> bool:
    """Записать дату выписки в черновики (PatientStationarWithoutBeds) по direction_id."""
    if not direction_pk or not discharge_date:
        return False
    rows = list(PatientStationarWithoutBeds.objects.filter(direction_id=direction_pk))
    if not rows:
        return False
    for pswb in rows:
        _apply_discharge_date_to_without_bed(pswb, discharge_date)
    return True


def sync_patient_to_bed_discharge_date_from_extract(iss: Issledovaniya) -> bool:
    """
    При подтверждении выписки записать plan_date_out и date_out в PatientToBed
    и PatientStationarWithoutBeds по direction_id из поля CDA «в.э.-Дата выписки» / «Дата выписки».
    """
    if not iss or not iss.research.is_extract:
        return False

    direction_pk = hosp_get_curent_hosp_dir(iss.pk)
    if not direction_pk:
        direction_pk = iss.napravleniye_id
    if not direction_pk:
        return False

    discharge_date = _read_discharge_date_from_protocol(iss)
    if not discharge_date:
        return False

    updated = False
    ptb = PatientToBed.objects.filter(direction_id=direction_pk).order_by("-pk").first()
    if ptb:
        apply_discharge_dates_to_hosp_record(ptb, discharge_date)
        updated = True
    if sync_patient_without_bed_discharge_date(direction_pk, discharge_date):
        updated = True
    iss.medical_examination = discharge_date
    iss.save()
    return updated
