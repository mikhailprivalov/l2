"""Синхронизация plan_date_out и date_out из протоколов выписки (is_extract_service)."""

from django.core.management.base import BaseCommand

from api.chambers.discharge_sync import (
    apply_discharge_out_dates_only,
    get_discharge_date_for_direction_by_extract_service,
    has_confirmed_extract_service_for_direction,
)
from podrazdeleniya.models import PatientStationarWithoutBeds, PatientToBed


class Command(BaseCommand):
    help = (
        "Для записей PatientToBed и PatientStationarWithoutBeds с direction_id "
        "ищет подтверждённую дочернюю услугу is_extract_service, читает «Дата выписки» "
        "и записывает plan_date_out и date_out."
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

    def handle(self, *args, **options):
        direction_pk_filter = options.get("direction_pk")
        dry_run = bool(options.get("dry_run"))

        ptb_qs = PatientToBed.objects.filter(direction_id__isnull=False)
        pswb_qs = PatientStationarWithoutBeds.objects.filter(direction_id__isnull=False)
        if direction_pk_filter:
            ptb_qs = ptb_qs.filter(direction_id=direction_pk_filter)
            pswb_qs = pswb_qs.filter(direction_id=direction_pk_filter)

        direction_pks = set(ptb_qs.values_list("direction_id", flat=True).distinct())
        direction_pks.update(pswb_qs.values_list("direction_id", flat=True).distinct())

        if not direction_pks:
            self.stdout.write("Нет записей с direction_id для обработки.")
            return

        updated_ptb = 0
        updated_pswb = 0
        skipped_no_extract = 0
        skipped_no_date = 0

        for direction_pk in sorted(direction_pks):
            discharge_date = get_discharge_date_for_direction_by_extract_service(direction_pk)
            if discharge_date is None:
                if has_confirmed_extract_service_for_direction(direction_pk):
                    skipped_no_date += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"direction_pk={direction_pk}: выписка подтверждена, дата в протоколе не найдена",
                        ),
                    )
                else:
                    skipped_no_extract += 1
                continue

            for ptb in ptb_qs.filter(direction_id=direction_pk):
                if dry_run:
                    if ptb.plan_date_out != discharge_date or ptb.date_out != discharge_date:
                        self.stdout.write(
                            f"[dry-run] PatientToBed pk={ptb.pk} direction={direction_pk} " f"→ plan_date_out/date_out={discharge_date}",
                        )
                        updated_ptb += 1
                elif apply_discharge_out_dates_only(ptb, discharge_date):
                    updated_ptb += 1
                    self.stdout.write(
                        f"PatientToBed pk={ptb.pk} direction={direction_pk} " f"→ plan_date_out/date_out={discharge_date}",
                    )

            for pswb in pswb_qs.filter(direction_id=direction_pk):
                if dry_run:
                    if pswb.plan_date_out != discharge_date or pswb.date_out != discharge_date:
                        self.stdout.write(
                            f"[dry-run] PatientStationarWithoutBeds pk={pswb.pk} direction={direction_pk} "
                            f"→ plan_date_out/date_out={discharge_date}",
                        )
                        updated_pswb += 1
                elif apply_discharge_out_dates_only(pswb, discharge_date):
                    updated_pswb += 1
                    self.stdout.write(
                        f"PatientStationarWithoutBeds pk={pswb.pk} direction={direction_pk} "
                        f"→ plan_date_out/date_out={discharge_date}",
                    )

        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}Готово: PatientToBed обновлено {updated_ptb}, "
                f"PatientStationarWithoutBeds обновлено {updated_pswb}, "
                f"без выписки {skipped_no_extract}, без даты в протоколе {skipped_no_date}",
            ),
        )
