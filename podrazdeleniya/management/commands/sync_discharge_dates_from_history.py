"""Синхронизация дат госпитализации: исторические записи и протоколы выписки."""

import datetime

from django.core.management.base import BaseCommand
from django.db.models import Q

from api.chambers.discharge_sync import (
    HISTORICAL_HOSP_PERIOD_START,
    HISTORICAL_HOSP_START_CUTOFF,
    apply_discharge_out_dates_only,
    apply_historical_hosp_period_dates,
    has_confirmed_extract_service_for_direction,
    hosp_record_starts_before_cutoff,
    resolve_discharge_out_date_for_hosp_record,
)
from podrazdeleniya.models import PatientStationarWithoutBeds, PatientToBed


class Command(BaseCommand):
    help = (
        "Обновляет даты в PatientToBed и PatientStationarWithoutBeds. "
        f"Исторические (plan_date_in или date_in < {HISTORICAL_HOSP_START_CUTOFF:%d.%m.%Y}): "
        f"date_in, plan_date_in, plan_date_out, date_out по одному дню с "
        f"{HISTORICAL_HOSP_PERIOD_START:%d.%m.%Y} (+1 день на запись), is_extract=True. "
        "Остальные — plan_date_out/date_out из выписки is_extract_service, is_extract=True."
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

    def _collect_historical_records(self, ptb_qs, pswb_qs):
        historical_filter = Q(plan_date_in__lt=HISTORICAL_HOSP_START_CUTOFF) | Q(
            date_in__lt=HISTORICAL_HOSP_START_CUTOFF,
        )
        items = []
        for ptb in ptb_qs.filter(historical_filter).order_by("pk"):
            if hosp_record_starts_before_cutoff(ptb):
                items.append(("PatientToBed", ptb))
        for pswb in pswb_qs.filter(historical_filter).order_by("pk"):
            if hosp_record_starts_before_cutoff(pswb):
                items.append(("PatientStationarWithoutBeds", pswb))
        return items

    def _process_historical_sequential(self, historical_items, dry_run):
        updated = 0
        period_date = HISTORICAL_HOSP_PERIOD_START
        for model_label, record in historical_items:
            if period_date >= HISTORICAL_HOSP_START_CUTOFF:
                self.stdout.write(
                    self.style.ERROR(
                        f"Достигнут предел {HISTORICAL_HOSP_START_CUTOFF:%d.%m.%Y}: " f"не хватило дней для {model_label} pk={record.pk}",
                    ),
                )
                break
            if dry_run:
                if not (
                    record.date_in == period_date and record.plan_date_in == period_date and record.plan_date_out == period_date and record.date_out == period_date and record.is_extract
                ):
                    updated += 1
                    self.stdout.write(
                        f"[dry-run] {model_label} pk={record.pk} " f"direction={getattr(record, 'direction_id', None)} " f"(historical-seq) → все даты={period_date}, is_extract=True",
                    )
            elif apply_historical_hosp_period_dates(record, period_date):
                updated += 1
                self.stdout.write(
                    f"{model_label} pk={record.pk} "
                    f"direction={getattr(record, 'direction_id', None)} "
                    f"(historical-seq) → все даты={period_date}, is_extract=True",
                )
            period_date += datetime.timedelta(days=1)
        return updated

    def _process_extract_record(self, record, model_label, dry_run, counters):
        if hosp_record_starts_before_cutoff(record):
            return

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

        if record.plan_date_out == discharge_date and record.date_out == discharge_date and record.is_extract:
            return

        if dry_run:
            counters["updated"] += 1
            self.stdout.write(
                f"[dry-run] {model_label} pk={record.pk} "
                f"direction={getattr(record, 'direction_id', None)} "
                f"(extract-service) → plan_date_out/date_out={discharge_date}, is_extract=True",
            )
            return

        if apply_discharge_out_dates_only(record, discharge_date):
            counters["updated"] += 1
            self.stdout.write(
                f"{model_label} pk={record.pk} "
                f"direction={getattr(record, 'direction_id', None)} "
                f"(extract-service) → plan_date_out/date_out={discharge_date}, is_extract=True",
            )

    def handle(self, *args, **options):
        direction_pk_filter = options.get("direction_pk")
        dry_run = bool(options.get("dry_run"))

        ptb_qs = self._base_ptb_qs(direction_pk_filter)
        pswb_qs = self._base_pswb_qs(direction_pk_filter)

        historical_items = self._collect_historical_records(ptb_qs, pswb_qs)
        historical_ptb_pks = {r.pk for label, r in historical_items if label == "PatientToBed"}
        historical_pswb_pks = {r.pk for label, r in historical_items if label == "PatientStationarWithoutBeds"}

        has_extract = (
            ptb_qs.filter(direction_id__isnull=False).exclude(pk__in=historical_ptb_pks).exists() or pswb_qs.filter(direction_id__isnull=False).exclude(pk__in=historical_pswb_pks).exists()
        )
        if not historical_items and not has_extract:
            self.stdout.write("Нет записей для обработки.")
            return

        prefix = "[dry-run] " if dry_run else ""

        historical_updated = self._process_historical_sequential(historical_items, dry_run)
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}Исторических записей обновлено: {historical_updated} " f"(дни с {HISTORICAL_HOSP_PERIOD_START:%d.%m.%Y})",
            ),
        )

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

        for ptb in ptb_qs.filter(direction_id__isnull=False).exclude(pk__in=historical_ptb_pks).order_by("pk"):
            self._process_extract_record(ptb, "PatientToBed", dry_run, ptb_counters)

        for pswb in pswb_qs.filter(direction_id__isnull=False).exclude(pk__in=historical_pswb_pks).order_by("pk"):
            self._process_extract_record(pswb, "PatientStationarWithoutBeds", dry_run, pswb_counters)

        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}Выписка: PatientToBed {ptb_counters['updated']}, "
                f"PatientStationarWithoutBeds {pswb_counters['updated']}; "
                f"без выписки PTB={ptb_counters['skipped_no_extract']} "
                f"PSWB={pswb_counters['skipped_no_extract']}, "
                f"без даты PTB={ptb_counters['skipped_no_date']} PSWB={pswb_counters['skipped_no_date']}",
            ),
        )
