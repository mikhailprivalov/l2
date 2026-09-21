from django.core.management.base import BaseCommand
from django.db.models import Count, Value
from django.db.models.functions import Coalesce

from employees.models import Department, Employee, EmployeePosition, Position


MODEL_CHOICES = ("employee", "position", "department", "employee_position")


class Command(BaseCommand):
    help = "Поиск дубликатов Employee, Position, Department, EmployeePosition"

    def add_arguments(self, parser):
        parser.add_argument(
            "--hospital",
            type=int,
            default=None,
            help="ID организации (Hospitals.pk). Без параметра — все организации.",
        )
        parser.add_argument(
            "--model",
            action="append",
            choices=MODEL_CHOICES,
            dest="models",
            help="Какие модели проверить (можно указать несколько раз). По умолчанию — все.",
        )

    def handle(self, *args, **options):
        hospital_id = options.get("hospital")
        models = options.get("models") or list(MODEL_CHOICES)

        total_groups = 0
        if "employee" in models:
            total_groups += self._report_employees(hospital_id)
        if "position" in models:
            total_groups += self._report_positions(hospital_id)
        if "department" in models:
            total_groups += self._report_departments(hospital_id)
        if "employee_position" in models:
            total_groups += self._report_employee_positions(hospital_id)

        if total_groups == 0:
            self.stdout.write(self.style.SUCCESS("Дубликаты не найдены"))
        else:
            self.stdout.write(self.style.WARNING(f"Всего групп дубликатов: {total_groups}"))

    def _hospital_filter(self, qs, hospital_id, field="hospital_id"):
        if hospital_id is not None:
            return qs.filter(**{field: hospital_id})
        return qs

    def _report_employees(self, hospital_id):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Employee ==="))
        qs = self._hospital_filter(Employee.objects.all(), hospital_id)
        groups = (
            qs.values("hospital_id", "family", "name", "patronymic")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
            .order_by("hospital_id", "family", "name", "patronymic")
        )
        count = 0
        for group in groups:
            rows = list(
                Employee.objects.filter(
                    hospital_id=group["hospital_id"],
                    family=group["family"],
                    name=group["name"],
                    patronymic=group["patronymic"],
                )
                .order_by("pk")
                .values_list("pk", "is_active", "snils")
            )
            ids = ", ".join(str(row[0]) for row in rows)
            fio = f'{group["family"]} {group["name"]} {group["patronymic"] or ""}'.strip()
            self.stdout.write(
                f'hospital={group["hospital_id"]} | {fio} | count={group["cnt"]} | ids=[{ids}]'
            )
            count += 1
        if count == 0:
            self.stdout.write("нет дубликатов")
        return count

    def _report_positions(self, hospital_id):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Position ==="))
        qs = self._hospital_filter(Position.objects.all(), hospital_id)
        groups = (
            qs.values("hospital_id", "name")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
            .order_by("hospital_id", "name")
        )
        count = 0
        for group in groups:
            ids = list(
                Position.objects.filter(hospital_id=group["hospital_id"], name=group["name"])
                .order_by("pk")
                .values_list("pk", flat=True)
            )
            self.stdout.write(
                f'hospital={group["hospital_id"]} | {group["name"]} | count={group["cnt"]} | '
                f'ids=[{", ".join(map(str, ids))}]'
            )
            count += 1
        if count == 0:
            self.stdout.write("нет дубликатов")
        return count

    def _report_departments(self, hospital_id):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Department ==="))
        qs = self._hospital_filter(Department.objects.all(), hospital_id)
        groups = (
            qs.values("hospital_id", "name")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
            .order_by("hospital_id", "name")
        )
        count = 0
        for group in groups:
            ids = list(
                Department.objects.filter(hospital_id=group["hospital_id"], name=group["name"])
                .order_by("pk")
                .values_list("pk", flat=True)
            )
            self.stdout.write(
                f'hospital={group["hospital_id"]} | {group["name"]} | count={group["cnt"]} | '
                f'ids=[{", ".join(map(str, ids))}]'
            )
            count += 1
        if count == 0:
            self.stdout.write("нет дубликатов")
        return count

    def _report_employee_positions(self, hospital_id):
        self.stdout.write(self.style.MIGRATE_HEADING("=== EmployeePosition ==="))
        qs = EmployeePosition.objects.all()
        if hospital_id is not None:
            qs = qs.filter(employee__hospital_id=hospital_id)

        qs = qs.annotate(tabel_norm=Coalesce("tabel_number", Value("")))
        groups = (
            qs.values("employee_id", "position_id", "department_id", "is_active", "tabel_norm")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
            .order_by("employee_id", "position_id", "department_id", "is_active", "tabel_norm")
        )
        count = 0
        for group in groups:
            rows = (
                EmployeePosition.objects.filter(
                    employee_id=group["employee_id"],
                    position_id=group["position_id"],
                    department_id=group["department_id"],
                    is_active=group["is_active"],
                )
                .annotate(tabel_norm=Coalesce("tabel_number", Value("")))
                .filter(tabel_norm=group["tabel_norm"])
                .select_related("employee", "position", "department")
                .order_by("pk")
            )
            ids = []
            label = ""
            for row in rows:
                ids.append(str(row.pk))
                if not label:
                    fio = f"{row.employee.family} {row.employee.name} {row.employee.patronymic or ''}".strip()
                    tabel = group["tabel_norm"] or "—"
                    label = (
                        f"{fio} | {row.position.name} | {row.department.name} | "
                        f"active={row.is_active} | tabel={tabel}"
                    )
            self.stdout.write(f"{label} | count={group['cnt']} | ids=[{', '.join(ids)}]")
            count += 1
        if count == 0:
            self.stdout.write("нет дубликатов")
        return count
