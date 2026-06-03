"""Синхронизация plan_date_out/date_out по «Дата выписки» из is_extract_service за последние N дней."""

from django.core.management.base import BaseCommand

from api.chambers.discharge_sync import (
    RECENT_EXTRACT_SYNC_DAYS_DEFAULT,
    sync_discharge_out_dates_recent_period,
)


class Command(BaseCommand):
    help = (
        "За период [сегодня − N дней, сегодня] по direction_id ищет подтверждённые дочерние "
        "услуги is_extract_service, читает «Дата выписки» из протокола и записывает "
        "plan_date_out и date_out в PatientToBed и PatientStationarWithoutBeds."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=RECENT_EXTRACT_SYNC_DAYS_DEFAULT,
            help=f"Глубина периода в днях (по умолчанию {RECENT_EXTRACT_SYNC_DAYS_DEFAULT})",
        )
        parser.add_argument(
            "--direction-pk",
            type=int,
            default=None,
            help="Обработать только указанное направление",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только показать статистику, без сохранения",
        )

    def handle(self, *args, **options):
        days = options["days"]
        direction_pk = options.get("direction_pk")
        dry_run = bool(options.get("dry_run"))

        stats = sync_discharge_out_dates_recent_period(
            days=days,
            dry_run=dry_run,
            direction_pk=direction_pk,
        )

        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(
            f"{prefix}Период по дате выписки в протоколе: " f"{stats['date_from']:%d.%m.%Y} — {stats['date_to']:%d.%m.%Y}",
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}Направлений с выпиской в периоде: {stats['directions_with_discharge']}; "
                f"обновлено PatientToBed: {stats['updated_ptb']}, "
                f"PatientStationarWithoutBeds: {stats['updated_pswb']}; "
                f"без даты в периоде: {stats['skipped_no_discharge']}",
            ),
        )
