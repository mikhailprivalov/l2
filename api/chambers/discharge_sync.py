"""Синхронизация даты выписки из протокола в PatientToBed."""

import datetime

from django.utils.dateparse import parse_date

from directions.models import Issledovaniya, ParaclinicResult
from external_system.models import CdaFields
from podrazdeleniya.models import PatientToBed
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


def sync_patient_to_bed_discharge_date_from_extract(iss: Issledovaniya) -> bool:
    """
    При подтверждении выписки записать plan_date_out и date_out в PatientToBed
    по direction_id госпитализации из поля CDA «в.э.-Дата выписки».
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

    ptb = (
        PatientToBed.objects.filter(direction_id=direction_pk)
        .order_by("-pk")
        .first()
    )
    if not ptb:
        return False

    ptb.plan_date_out = discharge_date
    ptb.date_out = discharge_date
    ptb.save(update_fields=["plan_date_out", "date_out"])
    return True
