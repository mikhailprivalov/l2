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


def get_discharge_date_for_direction_by_extract_service(direction_pk):
    """Дата выписки из подтверждённой дочерней услуги с is_extract_service."""
    if not direction_pk:
        return None
    for extract_iss in (
        Issledovaniya.objects.filter(time_confirmation__isnull=False)
        .filter(Q(napravleniye_id=direction_pk) | Q(napravleniye__parent_id=direction_pk))
        .select_related("research")
        .order_by("-time_confirmation")
    ):
        if extract_iss.research.is_extract_service:
            discharge_date = _read_discharge_date_from_protocol(extract_iss)
            if discharge_date:
                return discharge_date
    return None


def has_confirmed_extract_service_for_direction(direction_pk) -> bool:
    if not direction_pk:
        return False
    return (
        Issledovaniya.objects.filter(
            time_confirmation__isnull=False,
            research__is_extract_service=True,
        )
        .filter(
            Q(napravleniye_id=direction_pk) | Q(napravleniye__parent_id=direction_pk),
        )
        .exists()
    )


HISTORICAL_HOSP_START_CUTOFF = datetime.date(2026, 5, 1)
HISTORICAL_HOSP_PERIOD_START = datetime.date(2010, 1, 1)


def hosp_record_starts_before_cutoff(record) -> bool:
    """date_in или plan_date_in строго раньше 01.05.2026."""
    if record.plan_date_in and record.plan_date_in < HISTORICAL_HOSP_START_CUTOFF:
        return True
    if record.date_in and record.date_in < HISTORICAL_HOSP_START_CUTOFF:
        return True
    return False


def apply_historical_hosp_period_dates(record, period_date: datetime.date) -> bool:
    """
    Для исторической записи: все четыре даты = period_date (распределение по дням с 01.01.2010),
    is_extract=True.
    """
    if period_date >= HISTORICAL_HOSP_START_CUTOFF:
        return False
    if record.date_in == period_date and record.plan_date_in == period_date and record.plan_date_out == period_date and record.date_out == period_date and record.is_extract:
        return False
    record.date_in = period_date
    record.plan_date_in = period_date
    record.plan_date_out = period_date
    record.date_out = period_date
    record.is_extract = True
    record.save(update_fields=["date_in", "plan_date_in", "plan_date_out", "date_out", "is_extract"])
    return True


def resolve_discharge_out_date_for_hosp_record(record):
    """
    Дата окончания для записи койки/черновика (только plan/date_out):
    — до 01.05.2026 обрабатывается apply_historical_hosp_period_dates;
    — иначе из подтверждённой выписки is_extract_service по direction_id.
    """
    if hosp_record_starts_before_cutoff(record):
        return None
    direction_pk = getattr(record, "direction_id", None)
    if direction_pk:
        return get_discharge_date_for_direction_by_extract_service(direction_pk)
    return None


def apply_discharge_out_dates_only(record, discharge_date) -> bool:
    """Записать plan_date_out, date_out и is_extract=True из протокола выписки."""
    if not discharge_date:
        return False
    if record.plan_date_out == discharge_date and record.date_out == discharge_date and record.is_extract:
        return False
    record.plan_date_out = discharge_date
    record.date_out = discharge_date
    record.is_extract = True
    record.save(update_fields=["plan_date_out", "date_out", "is_extract"])
    return True


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


RECENT_EXTRACT_SYNC_DAYS_DEFAULT = 30


def _hosp_direction_pk_from_extract_iss(iss: Issledovaniya):
    nap = iss.napravleniye
    if not nap:
        return None
    if nap.parent_id:
        return nap.parent_id
    return nap.pk


def collect_direction_pks_for_recent_extract_sync(
    date_from: datetime.date,
    date_to: datetime.date,
    direction_pk=None,
):
    """
    Направления для синхронизации: записи койки/черновики и выписки is_extract_service,
    у которых «Дата выписки» в протоколе попадает в [date_from, date_to].
    """
    direction_pks = set()
    if direction_pk:
        direction_pks.add(direction_pk)

    ptb_qs = PatientToBed.objects.filter(direction_id__isnull=False)
    pswb_qs = PatientStationarWithoutBeds.objects.filter(direction_id__isnull=False)
    if direction_pk:
        ptb_qs = ptb_qs.filter(direction_id=direction_pk)
        pswb_qs = pswb_qs.filter(direction_id=direction_pk)
    direction_pks.update(ptb_qs.values_list("direction_id", flat=True))
    direction_pks.update(pswb_qs.values_list("direction_id", flat=True))

    extract_qs = (
        Issledovaniya.objects.filter(time_confirmation__isnull=False)
        .filter(research__is_extract_service=True)
        .select_related("napravleniye")
    )
    if direction_pk:
        extract_qs = extract_qs.filter(
            Q(napravleniye_id=direction_pk) | Q(napravleniye__parent_id=direction_pk),
        )

    for extract_iss in extract_qs.iterator():
        discharge_date = _read_discharge_date_from_protocol(extract_iss)
        if not discharge_date or discharge_date < date_from or discharge_date > date_to:
            continue
        dir_pk = _hosp_direction_pk_from_extract_iss(extract_iss)
        if dir_pk:
            direction_pks.add(dir_pk)

    return direction_pks


def get_discharge_date_from_extract_service_by_protocol_date_in_period(direction_pk, date_from: datetime.date, date_to: datetime.date):
    """
    Дата выписки из подтверждённой is_extract_service, если «Дата выписки»
    в протоколе попадает в [date_from, date_to]. Берётся самая поздняя дата в окне.
    """
    if not direction_pk or date_from > date_to:
        return None
    best_date = None
    best_confirmed = None
    for extract_iss in (
        Issledovaniya.objects.filter(time_confirmation__isnull=False)
        .filter(research__is_extract_service=True)
        .filter(Q(napravleniye_id=direction_pk) | Q(napravleniye__parent_id=direction_pk))
        .select_related("research")
        .order_by("-time_confirmation")
    ):
        discharge_date = _read_discharge_date_from_protocol(extract_iss)
        if not discharge_date or discharge_date < date_from or discharge_date > date_to:
            continue
        confirmed_at = extract_iss.time_confirmation
        if best_date is None or discharge_date > best_date or (
            discharge_date == best_date and confirmed_at and (best_confirmed is None or confirmed_at > best_confirmed)
        ):
            best_date = discharge_date
            best_confirmed = confirmed_at
    return best_date


def apply_extract_service_out_dates_recent(record, discharge_date) -> bool:
    """plan_date_out, date_out и is_extract=True (без изменения дат заезда)."""
    if not discharge_date:
        return False
    if (
        record.plan_date_out == discharge_date
        and record.date_out == discharge_date
        and record.is_extract
    ):
        return False
    record.plan_date_out = discharge_date
    record.date_out = discharge_date
    record.is_extract = True
    record.save(update_fields=["plan_date_out", "date_out", "is_extract"])
    return True


def sync_discharge_out_dates_recent_period(
    days: int = RECENT_EXTRACT_SYNC_DAYS_DEFAULT,
    dry_run: bool = False,
    direction_pk=None,
):
    """
    За период [сегодня − days, сегодня]: по direction_id ищет is_extract_service,
    дату «Дата выписки» в протоколе и пишет plan_date_out, date_out, is_extract в PTB и PSWB.
    """
    from django.utils import timezone

    date_to = timezone.localdate()
    date_from = date_to - datetime.timedelta(days=days)
    stats = {
        "date_from": date_from,
        "date_to": date_to,
        "directions_with_discharge": 0,
        "updated_ptb": 0,
        "updated_pswb": 0,
        "skipped_no_discharge": 0,
    }

    direction_pks = collect_direction_pks_for_recent_extract_sync(
        date_from,
        date_to,
        direction_pk=direction_pk,
    )

    for dir_pk in sorted(direction_pks):
        discharge_date = get_discharge_date_from_extract_service_by_protocol_date_in_period(
            dir_pk,
            date_from,
            date_to,
        )
        if not discharge_date:
            stats["skipped_no_discharge"] += 1
            continue
        stats["directions_with_discharge"] += 1

        for ptb in PatientToBed.objects.filter(direction_id=dir_pk):
            if dry_run:
                if (
                    ptb.plan_date_out != discharge_date
                    or ptb.date_out != discharge_date
                    or not ptb.is_extract
                ):
                    stats["updated_ptb"] += 1
            elif apply_extract_service_out_dates_recent(ptb, discharge_date):
                stats["updated_ptb"] += 1

        for pswb in PatientStationarWithoutBeds.objects.filter(direction_id=dir_pk):
            if dry_run:
                if (
                    pswb.plan_date_out != discharge_date
                    or pswb.date_out != discharge_date
                    or not pswb.is_extract
                ):
                    stats["updated_pswb"] += 1
            elif apply_extract_service_out_dates_recent(pswb, discharge_date):
                stats["updated_pswb"] += 1

    return stats
