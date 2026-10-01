from django.db import transaction
from django.db.models import Count, Value
from django.db.models.functions import Coalesce

from employees.models import Employee, EmployeePosition
from users.models import DoctorProfileEmployeePosition


def reassign_employee_position_links(keeper_id, duplicate_ids):
    if not duplicate_ids:
        return
    for rel in EmployeePosition._meta.get_fields():
        if not getattr(rel, "one_to_many", False) and not getattr(rel, "one_to_one", False):
            continue
        field = getattr(rel, "field", None)
        if field is None or not getattr(field, "concrete", False):
            continue
        model = rel.related_model
        column = field.attname
        rows = model.objects.filter(**{f"{column}__in": duplicate_ids})
        if model is DoctorProfileEmployeePosition:
            for row in rows:
                already = model.objects.filter(doctor_profile_id=row.doctor_profile_id, employee_position_id=keeper_id).exclude(pk=row.pk).exists()
                if already:
                    row.delete()
                else:
                    row.employee_position_id = keeper_id
                    row.save(update_fields=["employee_position_id"])
            continue
        rows.update(**{column: keeper_id})


def _position_match(employee_id, position_id, department_id, is_active, tabel_norm, exclude_id=None):
    qs = (
        EmployeePosition.objects.filter(
            employee_id=employee_id,
            position_id=position_id,
            department_id=department_id,
            is_active=is_active,
        )
        .annotate(tabel_norm=Coalesce("tabel_number", Value("")))
        .filter(tabel_norm=tabel_norm)
        .order_by("pk")
    )
    if exclude_id is not None:
        qs = qs.exclude(pk=exclude_id)
    return qs.first()


def delete_employee_position_duplicates(hospital_id=None, stdout=None):
    qs = EmployeePosition.objects.all()
    if hospital_id is not None:
        qs = qs.filter(employee__hospital_id=hospital_id)
    qs = qs.annotate(tabel_norm=Coalesce("tabel_number", Value("")))
    groups = (
        qs.values("employee_id", "position_id", "department_id", "is_active", "tabel_norm")
        .annotate(cnt=Count("id"))
        .filter(cnt__gt=1)
        .order_by("employee_id", "position_id", "department_id")
    )
    deleted = 0
    with transaction.atomic():
        for group in groups:
            rows = list(
                EmployeePosition.objects.filter(
                    employee_id=group["employee_id"],
                    position_id=group["position_id"],
                    department_id=group["department_id"],
                    is_active=group["is_active"],
                )
                .annotate(tabel_norm=Coalesce("tabel_number", Value("")))
                .filter(tabel_norm=group["tabel_norm"])
                .order_by("pk")
            )
            if len(rows) < 2:
                continue
            keeper = rows[0]
            duplicate_ids = [row.pk for row in rows[1:]]
            reassign_employee_position_links(keeper.pk, duplicate_ids)
            EmployeePosition.objects.filter(pk__in=duplicate_ids).delete()
            deleted += len(duplicate_ids)
            if stdout is not None:
                stdout.write(f"EmployeePosition оставлена {keeper.pk}, удалены {duplicate_ids}")
    return deleted


def delete_employee_duplicates(hospital_id=None, stdout=None):
    qs = Employee.objects.all()
    if hospital_id is not None:
        qs = qs.filter(hospital_id=hospital_id)
    groups = qs.values("hospital_id", "family", "name", "patronymic").annotate(cnt=Count("id")).filter(cnt__gt=1).order_by("hospital_id", "family", "name", "patronymic")
    deleted = 0
    with transaction.atomic():
        for group in groups:
            rows = list(
                Employee.objects.filter(
                    hospital_id=group["hospital_id"],
                    family=group["family"],
                    name=group["name"],
                    patronymic=group["patronymic"],
                ).order_by("pk")
            )
            if len(rows) < 2:
                continue
            keeper = rows[0]
            duplicate_ids = []
            for duplicate in rows[1:]:
                for position in list(EmployeePosition.objects.filter(employee_id=duplicate.pk).order_by("pk")):
                    tabel_norm = position.tabel_number or ""
                    match = _position_match(
                        keeper.pk,
                        position.position_id,
                        position.department_id,
                        position.is_active,
                        tabel_norm,
                        exclude_id=position.pk,
                    )
                    if match:
                        reassign_employee_position_links(match.pk, [position.pk])
                        position.delete()
                    else:
                        position.employee_id = keeper.pk
                        position.save(update_fields=["employee_id"])
                duplicate_ids.append(duplicate.pk)
                duplicate.delete()
            deleted += len(duplicate_ids)
            if stdout is not None:
                fio = f'{group["family"]} {group["name"]} {group["patronymic"] or ""}'.strip()
                stdout.write(f"Employee оставлена {keeper.pk} ({fio}), удалены {duplicate_ids}")
    return deleted


def delete_same_employee_positions(hospital_id=None, stdout=None):
    qs = EmployeePosition.objects.all()
    if hospital_id is not None:
        qs = qs.filter(employee__hospital_id=hospital_id)
    group_fields = (
        "department_id",
        "employee__hospital_id",
        "employee__family",
        "employee__name",
        "employee__patronymic",
        "position__name",
        "rate",
        "is_active",
    )
    groups = qs.values(*group_fields).annotate(cnt=Count("id")).filter(cnt__gt=1).order_by("department_id", "employee__family", "employee__name", "position__name")
    deleted = 0
    with transaction.atomic():
        for group in groups:
            rows = list(
                EmployeePosition.objects.filter(
                    department_id=group["department_id"],
                    employee__hospital_id=group["employee__hospital_id"],
                    employee__family=group["employee__family"],
                    employee__name=group["employee__name"],
                    employee__patronymic=group["employee__patronymic"],
                    position__name=group["position__name"],
                    rate=group["rate"],
                    is_active=group["is_active"],
                )
                .select_related("employee", "position")
                .order_by("pk")
            )
            if len(rows) < 2:
                continue
            keeper = rows[0]
            duplicate_ids = [row.pk for row in rows[1:]]
            reassign_employee_position_links(keeper.pk, duplicate_ids)
            EmployeePosition.objects.filter(pk__in=duplicate_ids).delete()
            deleted += len(duplicate_ids)
            if stdout is not None:
                fio = f"{keeper.employee.family} {keeper.employee.name} {keeper.employee.patronymic or ''}".strip()
                stdout.write(f"EmployeePosition оставлена {keeper.pk} ({fio} | {keeper.position.name} | ставка {keeper.rate}), удалены {duplicate_ids}")
    return deleted
