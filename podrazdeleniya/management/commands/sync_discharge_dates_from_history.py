"""Синхронизация plan_date_out и date_out: исторические записи и протоколы выписки."""

from django.core.management.base import BaseCommand
from django.db.models import Q

from api.chambers.discharge_sync import (
    HISTORICAL_HOSP_FIXED_DISCHARGE,
    HISTORICAL_HOSP_START_CUTOFF,
    apply_discharge_out_dates_only,
    has_confirmed_extract_service_for_direction,
    hosp_record_starts_before_cutoff,
    resolve_discharge_out_date_for_hosp_record,
)
from podrazdeleniya.models import PatientStationarWithoutBeds, PatientToBed


class Command(BaseCommand):
    help = (
        "Обновляет plan_date_out и date_out в PatientToBed и PatientStationarWithoutBeds. "
        f"Если plan_date_in или date_in раньше {HISTORICAL_HOSP_START_CUTOFF:%d.%m.%Y}, "
        f"проставляет {HISTORICAL_HOSP_FIXED_DISCHARGE:%d.%m.%Y}. "
        "Иначе — дата из подтверждённой дочерней услуги is_extract_service (поле «Дата выписки»)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--direction-pk",
            type=int,
            default=None,
            help="Обработать только указанное направление",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только показать изменения, без сохранения",
        )

    def _base_ptb_qs(self, direction_pk_filter):
        qs = PatientToBed.objects.all()
        if direction_pk_filter:
            qs = qs.filter(direction_id=direction_pk_filter)
        return qs

    def _base_pswb_qs(self, direction_pk_filter):
        qs = PatientStationarWithoutBeds.objects.all()
        if direction_pk_filter:
            qs = qs.filter(direction_id=direction_pk_filter)
        return qs

    def _process_record(self, record, model_label, dry_run, counters):
        discharge_date = resolve_discharge_out_date_for_hosp_record(record)
        if discharge_date is None:
            if getattr(record, "direction_id", None):
                if has_confirmed_extract_service_for_direction(record.direction_id):
                    counters["skipped_no_date"] += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"{model_label} pk={record.pk} direction={record.direction_id}: " "выписка подтверждена, дата в протоколе не найдена",
                        ),
                    )
                else:
                    counters["skipped_no_extract"] += 1
            else:
                counters["skipped_no_direction"] += 1
            return

        if record.plan_date_out == discharge_date and record.date_out == discharge_date:
            return

        source = "historical-fixed" if hosp_record_starts_before_cutoff(record) else "extract-service"
        if dry_run:
            counters["updated"] += 1
            self.stdout.write(
                f"[dry-run] {model_label} pk={record.pk} " f"direction={getattr(record, 'direction_id', None)} " f"({source}) → plan_date_out/date_out={discharge_date}",
            )
            return

        if apply_discharge_out_dates_only(record, discharge_date):
            counters["updated"] += 1
            self.stdout.write(
                f"{model_label} pk={record.pk} " f"direction={getattr(record, 'direction_id', None)} " f"({source}) → plan_date_out/date_out={discharge_date}",
            )

    def handle(self, *args, **options):
        direction_pk_filter = options.get("direction_pk")
        dry_run = bool(options.get("dry_run"))

        ptb_qs = self._base_ptb_qs(direction_pk_filter)
        pswb_qs = self._base_pswb_qs(direction_pk_filter)

        historical_filter = Q(plan_date_in__lt=HISTORICAL_HOSP_START_CUTOFF) | Q(
            date_in__lt=HISTORICAL_HOSP_START_CUTOFF,
        )
        ptb_qs = ptb_qs.filter(historical_filter | Q(direction_id__isnull=False))
        pswb_qs = pswb_qs.filter(historical_filter | Q(direction_id__isnull=False))

        if not ptb_qs.exists() and not pswb_qs.exists():
            self.stdout.write("Нет записей для обработки.")
            return

        ptb_counters = {
            "updated": 0,
            "skipped_no_extract": 0,
            "skipped_no_date": 0,
            "skipped_no_direction": 0,
        }
        pswb_counters = {
            "updated": 0,
            "skipped_no_extract": 0,
            "skipped_no_date": 0,
            "skipped_no_direction": 0,
        }

        for ptb in ptb_qs.iterator():
            self._process_record(ptb, "PatientToBed", dry_run, ptb_counters)

        for pswb in pswb_qs.iterator():
            self._process_record(pswb, "PatientStationarWithoutBeds", dry_run, pswb_counters)

        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}Готово: PatientToBed обновлено {ptb_counters['updated']}, "
                f"PatientStationarWithoutBeds обновлено {pswb_counters['updated']}; "
                f"без выписки PTB={ptb_counters['skipped_no_extract']} PSWB={pswb_counters['skipped_no_extract']}, "
                f"без даты в протоколе PTB={ptb_counters['skipped_no_date']} PSWB={pswb_counters['skipped_no_date']}",
            ),
        )
