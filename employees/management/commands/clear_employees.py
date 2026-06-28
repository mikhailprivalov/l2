from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from employees.models import (
    CashRegister,
    Department,
    DoctorProfileDepartment,
    Employee,
    EmployeePosition,
    EmployeePositionCountWorkDayPerMonth,
    EmployeeVacation,
    EmployeeWorkingHoursSchedule,
    FactTimeWork,
    PlanDepartment,
    Position,
    TabelDocument,
    TabelFactTimeWorkRaw,
    TimeTrackingDocument,
    TimeTrackingStatus,
)
from hospitals.models import Hospitals
from users.models import DoctorProfileEmployeePosition


def deletion_steps_all():
    return [
        ("FactTimeWork", FactTimeWork.objects.all()),
        ("TabelFactTimeWorkRaw", TabelFactTimeWorkRaw.objects.all()),
        ("EmployeeWorkingHoursSchedule", EmployeeWorkingHoursSchedule.objects.all()),
        ("TimeTrackingStatus", TimeTrackingStatus.objects.all()),
        ("EmployeeVacation", EmployeeVacation.objects.all()),
        ("EmployeePositionCountWorkDayPerMonth", EmployeePositionCountWorkDayPerMonth.objects.all()),
        ("CashRegister", CashRegister.objects.all()),
        ("PlanDepartment", PlanDepartment.objects.all()),
        ("DoctorProfileDepartment", DoctorProfileDepartment.objects.all()),
        ("DoctorProfileEmployeePosition", DoctorProfileEmployeePosition.objects.all()),
        ("TabelDocument", TabelDocument.objects.all()),
        ("TimeTrackingDocument", TimeTrackingDocument.objects.all()),
        ("EmployeePosition", EmployeePosition.objects.all()),
        ("Employee", Employee.objects.all()),
        ("Department", Department.objects.all()),
        ("Position", Position.objects.all()),
    ]


def deletion_steps_for_organization(organization_id):
    department_ids = list(Department.objects.filter(hospital_id=organization_id).values_list("pk", flat=True))
    employee_position_ids = list(EmployeePosition.objects.filter(employee__hospital_id=organization_id).values_list("pk", flat=True))
    tabel_document_ids = list(TabelDocument.objects.filter(department_id__in=department_ids).values_list("pk", flat=True))

    time_tracking_document_ids = set(TimeTrackingDocument.objects.filter(department_id__in=department_ids).values_list("pk", flat=True))
    time_tracking_document_ids.update(
        EmployeeWorkingHoursSchedule.objects.filter(employee_position_id__in=employee_position_ids)
        .exclude(time_tracking_document_id__isnull=True)
        .values_list("time_tracking_document_id", flat=True)
    )
    time_tracking_document_ids = list(time_tracking_document_ids)

    return [
        ("FactTimeWork", FactTimeWork.objects.filter(tabel_document_id__in=tabel_document_ids)),
        ("TabelFactTimeWorkRaw", TabelFactTimeWorkRaw.objects.filter(tabel_document_id__in=tabel_document_ids)),
        ("FactTimeWork (по трудовым договорам)", FactTimeWork.objects.filter(employee_position_id__in=employee_position_ids)),
        ("EmployeeWorkingHoursSchedule", EmployeeWorkingHoursSchedule.objects.filter(time_tracking_document_id__in=time_tracking_document_ids)),
        ("EmployeeWorkingHoursSchedule (по трудовым договорам)", EmployeeWorkingHoursSchedule.objects.filter(employee_position_id__in=employee_position_ids)),
        ("TimeTrackingStatus", TimeTrackingStatus.objects.filter(time_tracking_document_id__in=time_tracking_document_ids)),
        ("EmployeeVacation", EmployeeVacation.objects.filter(employee_position_id__in=employee_position_ids)),
        ("EmployeePositionCountWorkDayPerMonth", EmployeePositionCountWorkDayPerMonth.objects.filter(employee_position_id__in=employee_position_ids)),
        ("CashRegister", CashRegister.objects.filter(department_id__in=department_ids)),
        ("PlanDepartment", PlanDepartment.objects.filter(department_id__in=department_ids)),
        ("DoctorProfileDepartment", DoctorProfileDepartment.objects.filter(department_id__in=department_ids)),
        ("DoctorProfileEmployeePosition", DoctorProfileEmployeePosition.objects.filter(employee_position_id__in=employee_position_ids)),
        ("TabelDocument", TabelDocument.objects.filter(department_id__in=department_ids)),
        ("TimeTrackingDocument", TimeTrackingDocument.objects.filter(pk__in=time_tracking_document_ids)),
        ("EmployeePosition", EmployeePosition.objects.filter(employee__hospital_id=organization_id)),
        ("Employee", Employee.objects.filter(hospital_id=organization_id)),
        ("Department", Department.objects.filter(hospital_id=organization_id)),
        ("Position", Position.objects.filter(hospital_id=organization_id)),
    ]


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("organization_id", nargs="?", type=int, default=None, help="ID организации в БД (hospital_id)")
        parser.add_argument("--all", action="store_true", help="Удалить все записи во всех организациях")
        parser.add_argument("--dry-run", action="store_true", help="Показать количество записей без удаления")
        parser.add_argument("-y", "--noinput", action="store_true", help="Удалить без подтверждения")

    def handle(self, *args, **kwargs):
        organization_id = kwargs["organization_id"]
        delete_all = kwargs["all"]
        dry_run = kwargs["dry_run"]
        noinput = kwargs["noinput"]

        if delete_all and organization_id is not None:
            raise CommandError("Укажите organization_id или --all, но не оба варианта сразу")
        if not delete_all and organization_id is None:
            raise CommandError("Нужна организация либо --all")

        if delete_all:
            deletion_steps = deletion_steps_all()
            scope_label = "Полная очистка таблиц employees (все организации)"
        else:
            hospital = Hospitals.objects.filter(pk=organization_id).first()
            if not hospital:
                raise CommandError(f"Организация с id={organization_id} не найдена")
            deletion_steps = deletion_steps_for_organization(organization_id)
            hospital_title = hospital.short_title or hospital.title
            scope_label = f"Очистка таблиц employees: {hospital_title} (id={organization_id})"

        counts = {label: qs.count() for label, qs in deletion_steps}
        total = sum(counts.values())

        self.stdout.write(scope_label)
        for label, count in counts.items():
            if count:
                self.stdout.write(f"  {label}: {count}")

        if total == 0:
            self.stdout.write("Нет записей для удаления.")
            return

        if dry_run:
            self.stdout.write(f"Итого будет удалено: {total} (dry-run, изменений нет)")
            return

        if not noinput:
            if delete_all:
                prompt = f"Удалить все {total} записей во всех организациях? [y/N] "
            else:
                prompt = f"Удалить {total} записей организации id={organization_id}? [y/N] "
            answer = input(prompt)
            if answer.strip().lower() not in ("y", "yes", "д", "да"):
                self.stdout.write("Отменено.")
                return

        with transaction.atomic():
            deleted_total = 0
            for label, qs in deletion_steps:
                _, deleted_by_model = qs.delete()
                count = sum(deleted_by_model.values())
                if count:
                    self.stdout.write(f"  {label}: {count}")
                    deleted_total += count

        self.stdout.write(f"Готово. Удалено записей: {deleted_total}")
