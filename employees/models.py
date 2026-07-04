import calendar
import copy
import datetime
import json
from typing import Union, Optional

import pytz
from django.db import models
from django.core.paginator import Paginator
from django.utils.formats import date_format

from employees.sql_func import get_employee_position, get_employee_work_time, get_employee_fact_time_work
from employees.work_time_parse import (
    iter_changed_work_time_cells,
    normalize_work_day_status_id,
    parse_fact_start_end_datetimes,
    parse_schedule_start_end,
)
from hospitals.models import Hospitals
from laboratory.settings import TIME_ZONE, LUNCH_DURATION_BY_POSITIONS, WORK_DAYS_PER_WEEK_DEFAULT, EMPLOYEE_START_WORK_TIME_DEFAULT
from laboratory.utils import strfdatetime, current_time
from slog.models import Log
from users.models import DoctorProfile
from django.utils import timezone

from utils.dates import try_strptime
from utils.string import make_short_name_form


class Employee(models.Model):
    hospital = models.ForeignKey(Hospitals, on_delete=models.CASCADE, verbose_name='Медицинское учреждение')
    family = models.CharField(max_length=64, verbose_name='Фамилия')
    name = models.CharField(max_length=64, verbose_name='Имя')
    patronymic = models.CharField(max_length=64, verbose_name='Отчество', blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    doctorprofile_created = models.ForeignKey(
        'users.DoctorProfile', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Профиль пользователя, создавшего запись', related_name='employees_employee_created'
    )
    doctorprofile_updated = models.ForeignKey(
        'users.DoctorProfile', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Профиль пользователя, обновившего запись', related_name='employees_employee_updated'
    )
    snils = models.CharField(max_length=11, verbose_name="СНИЛС", help_text='12345678912', default=None, blank=True, null=True)

    def __str__(self):
        return f'{self.family} {self.name} {self.patronymic} ({self.hospital})'.strip()

    @property
    def json(self):
        return {
            'id': self.id,
            'family': self.family,
            'name': self.name,
            'patronymic': self.patronymic,
            'hospitalId': self.hospital_id,
            'isActive': self.is_active,
            'createdAt': strfdatetime(self.created_at, "%d.%m.%Y %X"),
            'updatedAt': strfdatetime(self.updated_at, "%d.%m.%Y %X") if self.updated_at else None,
        }

    @staticmethod
    def get_json_by_id(hospital_id, id):
        try:
            return Employee.objects.get(id=id, hospital_id=hospital_id).json
        except Employee.DoesNotExist:
            return None

    @staticmethod
    def get_json_list(hospital_id, only_active=True, page=1, per_page=30, sort_column=None, sort_direction=None, filter=None):
        employees = Employee.objects.filter(hospital_id=hospital_id)
        if only_active:
            employees = employees.filter(is_active=True)
        if sort_column:
            employees = employees.order_by(f'{"-" if sort_direction == "desc" else ""}{sort_column}')
        if filter:
            filter = filter.strip()
        if filter:
            employees = employees.filter(models.Q(family__istartswith=filter) | models.Q(name__istartswith=filter) | models.Q(patronymic__istartswith=filter))
        paginator = Paginator(employees, per_page)
        return [employee.json for employee in paginator.get_page(page)]

    @staticmethod
    def add(hospital_id, family, name, patronymic, who_created, as_object=False):
        family, name, patronymic = Employee.normalize_values(family, name, patronymic)
        Employee.validate_values(hospital_id, family, name, patronymic)
        employee = Employee(hospital_id=hospital_id, family=family, name=name, patronymic=patronymic, doctorprofile_created=who_created)
        employee.save()
        Log.log(employee.pk, 121104, who_created, employee.json)
        if as_object:
            return employee
        return employee.json

    @staticmethod
    def edit(hospital_id, employee_id, family, name, patronymic, is_active, who_updated, as_object=False):
        family, name, patronymic = Employee.normalize_values(family, name, patronymic)
        employee = Employee.objects.get(id=employee_id, hospital_id=hospital_id)
        Employee.validate_values(employee.hospital_id, family, name, patronymic, current_id=employee_id)
        employee.family = family
        employee.name = name
        employee.patronymic = patronymic
        employee.is_active = is_active
        employee.doctorprofile_updated = who_updated
        employee.save()
        Log.log(employee.pk, 121105, who_updated, employee.json)
        if as_object:
            return employee
        return employee.json

    @staticmethod
    def normalize_values(family, name, patronymic):
        return family.strip(), name.strip(), patronymic.strip()

    @staticmethod
    def validate_values(hospital_id, family, name, patronymic, current_id=None):
        fields_with_errors = []
        if not family:
            fields_with_errors.append('фамилия')
        if not name:
            fields_with_errors.append('имя')
        if fields_with_errors:
            raise ValueError(f"Некорректно заполнены: {', '.join(fields_with_errors)}")

        if Employee.objects.filter(hospital_id=hospital_id, family=family, name=name, patronymic=patronymic).exclude(id=current_id).exists():
            raise ValueError('Такой сотрудник уже существует')

    @staticmethod
    def find_by_snils(snils: str, hospital_id: int):
        employee = Employee.objects.filter(snils=snils, hospital_id=hospital_id).first()
        return employee

    @staticmethod
    def create_employee(family, name, patronymic, snils, hospital_id: int, return_new: bool = False):
        new_employee = Employee(hospital_id=hospital_id, family=family, name=name, patronymic=patronymic, snils=snils)
        new_employee.save()
        if return_new:
            return new_employee

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        indexes = [
            models.Index(fields=['hospital', 'family', 'name', 'patronymic', 'is_active', 'snils']),
        ]
        unique_together = ('hospital', 'family', 'name', 'patronymic', 'is_active', 'snils')
        ordering = ('hospital__short_title', 'hospital__title', 'family', 'name', 'patronymic')


class Position(models.Model):
    hospital = models.ForeignKey(Hospitals, on_delete=models.CASCADE, verbose_name='Медицинское учреждение')
    name = models.CharField(max_length=128, verbose_name='Название должности')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    doctorprofile_created = models.ForeignKey(
        'users.DoctorProfile', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Профиль пользователя, создавшего запись', related_name='employees_position_created'
    )
    doctorprofile_updated = models.ForeignKey(
        'users.DoctorProfile', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Профиль пользователя, обновившего запись', related_name='employees_position_updated'
    )
    external_id = models.CharField(max_length=255, default=None, blank=True, null=True, help_text="Внешний ИД-код", db_index=True)

    def __str__(self):
        return self.name

    @property
    def json(self):
        return {
            'id': self.id,
            'name': self.name,
            'hospitalId': self.hospital_id,
            'isActive': self.is_active,
            'createdAt': strfdatetime(self.created_at, "%d.%m.%Y %X"),
            'updatedAt': strfdatetime(self.updated_at, "%d.%m.%Y %X") if self.updated_at else None,
        }

    @staticmethod
    def get_json_by_id(hospital_id, object_id):
        try:
            return Position.objects.get(id=object_id, hospital_id=hospital_id).json
        except Position.DoesNotExist:
            return None

    @staticmethod
    def get_json_list(hospital_id, only_active=True, page=1, per_page=30, sort_column=None, sort_direction=None, filter=None):
        positions = Position.objects.filter(hospital_id=hospital_id)
        if only_active:
            positions = positions.filter(is_active=True)
        if sort_column:
            positions = positions.order_by(f'{"-" if sort_direction == "desc" else ""}{sort_column}')
        if filter:
            filter = filter.strip()
        if filter:
            positions = positions.filter(models.Q(name__istartswith=filter))
        paginator = Paginator(positions, per_page)
        return [position.json for position in paginator.get_page(page)]

    @staticmethod
    def add(hospital_id, name, who_created):
        name = Position.normalize_values(name)
        Position.validate_values(hospital_id, name)
        position = Position(hospital_id=hospital_id, name=name, doctorprofile_created=who_created)
        position.save()
        Log.log(position.pk, 121102, who_created, position.json)
        return position.json

    @staticmethod
    def edit(hospital_id, position_id, name, is_active, who_updated):
        name = Position.normalize_values(name)
        position = Position.objects.get(id=position_id, hospital_id=hospital_id)
        Position.validate_values(position.hospital_id, name, position_id)
        position.name = name
        position.is_active = is_active
        position.doctorprofile_updated = who_updated
        position.save()
        Log.log(position.pk, 121103, who_updated, position.json)
        return position.json

    @staticmethod
    def normalize_values(name):
        return name.strip()

    @staticmethod
    def validate_values(hospital_id, name, current_id=None):
        if not name:
            raise ValueError('Название должности не указано')
        if Position.objects.filter(hospital_id=hospital_id, name=name).exclude(id=current_id).exists():
            raise ValueError('Должность с таким названием уже существует')

    @staticmethod
    def get_active(hospital_id: int = None):
        if not hospital_id:
            hospital_id = Hospitals.objects.get(is_default=True)
        positions = [{"id": position.pk, "label": position.name} for position in Position.objects.filter(is_active=True, hospital_id=hospital_id).order_by('name')]
        return positions or []

    @staticmethod
    def get_active_titles(hospital_id: int = None):
        if not hospital_id:
            hospital_id = Hospitals.objects.get(is_default=True)
        titles = set(Position.objects.filter(is_active=True, hospital_id=hospital_id).values_list('name', flat=True).order_by('name'))
        return titles

    @staticmethod
    def get_active_positions(hospital_id: int = None):
        if not hospital_id:
            hospital_id = Hospitals.objects.get(is_default=True)
        positions = Position.objects.filter(is_active=True, hospital_id=hospital_id).order_by('name')
        return positions

    @staticmethod
    def create_position(name: str, hospital_id: int = None, return_new: bool = False):
        if not hospital_id:
            hospital_id = Hospitals.objects.get(is_default=True)
        new_position = Position(hospital_id=hospital_id, name=name, is_active=True)
        new_position.save()
        if return_new:
            return new_position

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'
        indexes = [
            models.Index(fields=['hospital', 'name', 'is_active']),
        ]
        unique_together = ('hospital', 'name')
        ordering = ('hospital__short_title', 'hospital__title', 'name')


def default_work_start():
    hours, minutes = map(int, EMPLOYEE_START_WORK_TIME_DEFAULT.split(":"))
    return datetime.time(hours, minutes)


class Department(models.Model):
    hospital = models.ForeignKey(Hospitals, on_delete=models.CASCADE, verbose_name='Медицинское учреждение')
    name = models.CharField(max_length=255, verbose_name='Название отдела')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    doctorprofile_created = models.ForeignKey(
        'users.DoctorProfile', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Профиль пользователя, создавшего запись', related_name='employees_department_created'
    )
    doctorprofile_updated = models.ForeignKey(
        'users.DoctorProfile', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Профиль пользователя, обновившего запись', related_name='employees_department_updated'
    )
    external_id = models.CharField(max_length=255, default=None, blank=True, null=True, help_text="Внешний ИД-код", db_index=True)
    lunch_duration = models.PositiveSmallIntegerField(default=None, blank=True, null=True, help_text="30, 60, 120")
    work_start = models.TimeField(default=default_work_start, blank=True, null=True, help_text="08:00")

    def __str__(self):
        return self.name

    @property
    def json(self):
        return {
            'id': self.id,
            'name': self.name,
            'hospitalId': self.hospital_id,
            'isActive': self.is_active,
            'childrenElementsCount': EmployeePosition.objects.filter(department=self, is_active=True).count(),
            'createdAt': strfdatetime(self.created_at, "%d.%m.%Y %X"),
            'updatedAt': strfdatetime(self.updated_at, "%d.%m.%Y %X") if self.updated_at else None,
        }

    @staticmethod
    def get_by_id(hospital_id, object_id):
        try:
            return Department.objects.get(id=object_id, hospital_id=hospital_id)
        except Department.DoesNotExist:
            return None

    @staticmethod
    def get_json_by_id(hospital_id, object_id):
        department = Department.get_by_id(hospital_id, object_id)

        return department.json if department else None

    @staticmethod
    def get_json_list(hospital_id, only_active=True, page=1, per_page=30, sort_column=None, sort_direction=None, filter=None, return_total_rows=False):
        departments = Department.objects.filter(hospital_id=hospital_id)
        if only_active:
            departments = departments.filter(is_active=True)
        if sort_column:
            departments = departments.order_by(f'{"-" if sort_direction == "desc" else ""}{sort_column}')
        if filter:
            filter = filter.strip()
        if filter:
            departments = departments.filter(models.Q(name__istartswith=filter))

        rows = departments
        total_pages = 1
        if not return_total_rows:
            paginator = Paginator(departments, per_page)
            rows = paginator.get_page(page)
            total_pages = paginator.num_pages

        return [department.json for department in rows], total_pages

    @staticmethod
    def add(hospital_id, name, who_created):
        name = Department.normalize_values(name)
        Department.validate_values(hospital_id=hospital_id, name=name)
        department = Department(hospital_id=hospital_id, name=name, doctorprofile_created=who_created)
        department.save()
        Log.log(department.pk, 121100, who_created, department.json)
        return department.json

    @staticmethod
    def edit(hospital_id, department_id, name, is_active, who_updated):
        name = Department.normalize_values(name)
        department = Department.objects.get(id=department_id, hospital_id=hospital_id)
        Department.validate_values(hospital_id=department.hospital_id, name=name, current_id=department_id)
        department.name = name
        department.is_active = is_active
        department.doctorprofile_updated = who_updated
        department.save()
        Log.log(department.pk, 121101, who_updated, department.json)
        return department.json

    @staticmethod
    def normalize_values(name):
        return name.strip()

    @staticmethod
    def validate_values(hospital_id, name, current_id=None):
        if not name:
            raise ValueError('Название отдела не указано')

        departments = Department.objects.filter(hospital_id=hospital_id, name=name)
        if current_id:
            departments = departments.exclude(id=current_id)

        if departments.exists():
            raise ValueError('Отдел с таким названием уже существует')

    @staticmethod
    def get_active(hospital_id: int = None):
        if not hospital_id:
            hospital_id = Hospitals.objects.get(is_default=True)
        departments = [
            {"id": department.pk, "label": department.name, "lunchDuration": department.lunch_duration}
            for department in Department.objects.filter(is_active=True, hospital_id=hospital_id).order_by('name')
        ]
        return departments or []

    @staticmethod
    def get_active_titles(hospital_id: int = None):
        if not hospital_id:
            hospital_id = Hospitals.objects.get(is_default=True)
        titles = set(Department.objects.filter(is_active=True, hospital_id=hospital_id).values_list('name', flat=True).order_by('name'))
        return titles

    @staticmethod
    def get_active_departments(hospital_id: int = None):
        if not hospital_id:
            hospital_id = Hospitals.objects.get(is_default=True)
        departments = Department.objects.filter(is_active=True, hospital_id=hospital_id).order_by('name')
        return departments

    @staticmethod
    def create_department(name: str, hospital_id: int = None, return_new: bool = False):
        if not hospital_id:
            hospital_id = Hospitals.objects.get(is_default=True)
        new_department = Department(hospital_id=hospital_id, name=name, is_active=True)
        new_department.save()
        if return_new:
            return new_department

    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'
        indexes = [
            models.Index(fields=['hospital', 'name', 'is_active']),
        ]
        unique_together = ('hospital', 'name')
        ordering = ('hospital__short_title', 'hospital__title', 'name')

    @staticmethod
    def get_active_departments_for_user(user, hospital_id: int = None):
        if not hospital_id:
            hospital_id = Hospitals.objects.get(is_default=True)

        queryset = Department.objects.filter(
            is_active=True,
            hospital_id=hospital_id,
        ).order_by("name")

        if not user.is_superuser:
            allowed_ids = DoctorProfileDepartment.get_doctor_departments_ids(user.doctorprofile)
            queryset = queryset.filter(pk__in=allowed_ids)
        return [
            {
                "id": department.pk,
                "label": department.name,
                "lunchDuration": department.lunch_duration,
            }
            for department in queryset
        ]


class TypeWorkTimeEmployee(models.Model):
    title = models.CharField(max_length=255, help_text='Занятость (осн | внутр.свом| внеш. совм)')

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = 'Тип занятости'
        verbose_name_plural = 'Типы занятости'

    @staticmethod
    def get_active():
        typesWorkTime = [{"id": typeWorkTime.pk, "label": typeWorkTime.title} for typeWorkTime in TypeWorkTimeEmployee.objects.all().order_by('title')]
        return typesWorkTime or []


class EmployeePosition(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name='Сотрудник')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, verbose_name='Должность')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name='Отдел')
    rate = models.FloatField(verbose_name='Ставка')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    doctorprofile_created = models.ForeignKey(
        'users.DoctorProfile', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Профиль пользователя, создавшего запись', related_name='employees_employee_position_created'
    )
    doctorprofile_updated = models.ForeignKey(
        'users.DoctorProfile', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Профиль пользователя, обновившего запись', related_name='employees_employee_position_updated'
    )
    tabel_number = models.CharField(max_length=255, default=None, blank=True, null=True, help_text="Табельный номер", db_index=True)
    type_work_time = models.ForeignKey(TypeWorkTimeEmployee, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    external_id = models.CharField(max_length=255, default=None, blank=True, null=True, help_text="Внешний ИД-код", db_index=True)
    date_employment = models.DateField(verbose_name="Дата приема на работу", help_text="2025-01-11", blank=True, null=True, default=None)
    date_dismissal = models.DateField(verbose_name="Дата увольнения", help_text="2025-02-01", blank=True, null=True, default=None)
    lunch_duration = models.PositiveSmallIntegerField(default=None, blank=True, null=True, help_text="30, 60, 120")
    date_transfer = models.DateField(verbose_name="Дата перевода", help_text="2025-02-01", blank=True, null=True, default=None)
    daily_hours_norm = models.PositiveSmallIntegerField(default=None, blank=True, null=True, help_text="120, 240, 360, 480 мин")
    weekly_hours_norm = models.PositiveSmallIntegerField(default=None, blank=True, null=True, help_text="120, 240, 360, 480 мин")
    work_days_per_week = models.PositiveSmallIntegerField(default=WORK_DAYS_PER_WEEK_DEFAULT, blank=True, null=True, help_text="5 дней")
    work_start = models.TimeField(default=default_work_start, blank=True, null=True, help_text="08:00")

    def __str__(self):
        return f'{self.employee} — {self.position} (ставка {self.rate})'

    @property
    def json(self):
        return {
            'id': self.id,
            'employeeId': self.employee_id,
            'positionId': self.position_id,
            'departmentId': self.department_id,
            'rate': self.rate,
            'isActive': self.is_active,
            'createdAt': strfdatetime(self.created_at, "%d.%m.%Y %X"),
            'updatedAt': strfdatetime(self.updated_at, "%d.%m.%Y %X") if self.updated_at else None,
        }

    @staticmethod
    def get_json_by_id(hospital_id, object_id):
        try:
            return EmployeePosition.objects.get(id=object_id, employee__hospital_id=hospital_id).json
        except EmployeePosition.DoesNotExist:
            return None

    @staticmethod
    def get_json_list(employee_id, only_active=True, page=1, per_page=30, sort_column=None, sort_direction=None, filter=None):
        employee_positions = EmployeePosition.objects.filter(employee_id=employee_id)
        if only_active:
            employee_positions = employee_positions.filter(is_active=True)
        if sort_column:
            employee_positions = employee_positions.order_by(f'{"-" if sort_direction == "desc" else ""}{sort_column}')
        if filter:
            filter = filter.strip()
        if filter:
            employee_positions = employee_positions.filter(
                models.Q(employee__family__istartswith=filter) | models.Q(employee__name__istartswith=filter) | models.Q(employee__patronymic__istartswith=filter)
            )
        paginator = Paginator(employee_positions, per_page)
        return [employee_position.json for employee_position in paginator.get_page(page)]

    @staticmethod
    def _parse_form_date(value):
        if not value:
            return None
        parsed = try_strptime(value, formats=("%Y-%m-%d", "%d.%m.%Y"))
        return parsed.date() if parsed else None

    @staticmethod
    def _parse_form_time(value):
        if not value:
            return None
        parts = str(value).split(":")
        if len(parts) < 2:
            return None
        return datetime.time(int(parts[0]), int(parts[1]))

    @staticmethod
    def _parse_form_int(value):
        if value is None or value == "":
            return None
        return int(value)

    @staticmethod
    def apply_form_extended_fields(employee_position, form_values: dict):
        employee_position.tabel_number = (form_values.get("tabelNumber") or "").strip() or None

        type_work_time_id = form_values.get("typeWorkTimeId")
        if type_work_time_id in (None, "", -1, "-1"):
            employee_position.type_work_time_id = None
        else:
            employee_position.type_work_time_id = int(type_work_time_id)

        employee_position.date_employment = EmployeePosition._parse_form_date(form_values.get("dateEmployment"))
        employee_position.date_dismissal = EmployeePosition._parse_form_date(form_values.get("dateDismissal"))
        employee_position.date_transfer = EmployeePosition._parse_form_date(form_values.get("dateTransfer"))
        employee_position.lunch_duration = EmployeePosition._parse_form_int(form_values.get("lunchDuration"))
        employee_position.daily_hours_norm = EmployeePosition._parse_form_int(form_values.get("dailyHoursNorm"))
        employee_position.weekly_hours_norm = EmployeePosition._parse_form_int(form_values.get("weeklyHoursNorm"))
        employee_position.work_days_per_week = EmployeePosition._parse_form_int(form_values.get("workDaysPerWeek"))
        employee_position.work_start = EmployeePosition._parse_form_time(form_values.get("workStart"))

    @staticmethod
    def _tabel_number_from_form(form_values):
        if not form_values:
            return None
        return (form_values.get("tabelNumber") or "").strip() or None

    @staticmethod
    def add(hospital_id, employee_id, position_id, department_id, rate, who_created, form_values=None):
        tabel_number = EmployeePosition._tabel_number_from_form(form_values)
        EmployeePosition.validate_values(employee_id, position_id, department_id, rate, is_active=True, tabel_number=tabel_number)
        position = Position.objects.get(id=position_id, hospital_id=hospital_id)
        department = Department.objects.get(id=department_id, hospital_id=hospital_id)
        employee_position = EmployeePosition(employee_id=employee_id, position=position, department=department, rate=rate, doctorprofile_created=who_created)
        if form_values:
            EmployeePosition.apply_form_extended_fields(employee_position, form_values)
        employee_position.save()
        Log.log(employee_position.pk, 121106, who_created, employee_position.json)
        return employee_position.json

    @staticmethod
    def edit(hospital_id, employee_position_id, position_id, department_id, rate, is_active, who_updated, form_values=None):
        employee_position = EmployeePosition.objects.get(id=employee_position_id, employee__hospital_id=hospital_id)
        employee_id = int(form_values.get("employeeId") or employee_position.employee_id) if form_values else employee_position.employee_id
        tabel_number = EmployeePosition._tabel_number_from_form(form_values) if form_values else employee_position.tabel_number

        unique_fields_changed = (
            employee_id != employee_position.employee_id
            or position_id != employee_position.position_id
            or department_id != employee_position.department_id
            or is_active != employee_position.is_active
            or tabel_number != employee_position.tabel_number
        )
        if unique_fields_changed:
            EmployeePosition.validate_values(
                employee_id,
                position_id,
                department_id,
                rate,
                current_id=employee_position_id,
                is_active=is_active,
                tabel_number=tabel_number,
            )

        position = Position.objects.get(id=position_id, hospital_id=hospital_id)
        department = Department.objects.get(id=department_id, hospital_id=hospital_id)
        employee_position.employee_id = employee_id
        employee_position.position = position
        employee_position.department = department
        employee_position.rate = rate
        employee_position.is_active = is_active
        employee_position.doctorprofile_updated = who_updated
        if form_values:
            EmployeePosition.apply_form_extended_fields(employee_position, form_values)
        employee_position.save()
        Log.log(employee_position.pk, 121107, who_updated, employee_position.json)
        return employee_position.json

    @staticmethod
    def validate_values(employee_id, position_id, department_id, rate, current_id=None, is_active=True, tabel_number=None):
        employee_position_qs = EmployeePosition.objects.filter(
            employee_id=employee_id,
            position_id=position_id,
            department_id=department_id,
            is_active=is_active,
        )
        if tabel_number:
            employee_position_qs = employee_position_qs.filter(tabel_number=tabel_number)
        else:
            employee_position_qs = employee_position_qs.filter(models.Q(tabel_number__isnull=True) | models.Q(tabel_number=""))

        if current_id:
            employee_position_qs = employee_position_qs.exclude(id=current_id)

        if employee_position_qs.exists():
            raise ValueError('Такая должность уже существует')
        if rate < 0:
            raise ValueError('Ставка не может быть отрицательной')

    @staticmethod
    def get_employee_position(org_id: int, department_ids: list, position_ids: list, employment_form_ids: list):
        department_ids_tuple = tuple(department_ids) if department_ids else tuple([None])
        position_ids_tuple = tuple(position_ids) if position_ids else tuple([None])
        employment_form_ids_tuple = tuple(employment_form_ids) if employment_form_ids else tuple([None])
        employees = get_employee_position(org_id, department_ids_tuple, position_ids_tuple, employment_form_ids_tuple)
        result = [
            {
                "employeeId": employee.employee_position_id,
                "employmentForm": employee.employment_form,
                "snils": employee.snils,
                "tabelNumber": employee.tabel_number,
                "employeeFio": f"{employee.employee_family} {employee.employee_name} {employee.employee_patronymic}",
                "department": employee.department_title,
                "position": employee.position_title,
                "rate": employee.rate,
                "dateEmployment": employee.date_employment.strftime("%d.%m.%Y") if employee.date_employment else None,
                "dateDismissal": employee.date_dismissal.strftime("%d.%m.%Y") if employee.date_dismissal else None,
            }
            for employee in employees
        ]
        return result

    @staticmethod
    def find_employee_position(active: True, employee: Employee, position: Position, deparment: Department, tabel_number: str):
        employee_position = EmployeePosition.objects.filter(is_active=active, employee_id=employee.pk, position_id=position.pk, department_id=deparment.pk, tabel_number=tabel_number).first()
        return employee_position

    @staticmethod
    def all_by_organization(org_id: int):
        employee_positions = EmployeePosition.objects.filter(employee__hospital_id=org_id).select_related('employee')
        return employee_positions

    class Meta:
        verbose_name = 'Должность сотрудника'
        verbose_name_plural = 'Должности сотрудников'
        indexes = [
            models.Index(fields=['employee', 'position', 'department', 'rate', 'is_active', 'tabel_number']),
        ]
        unique_together = ('employee', 'position', 'department', 'is_active', 'tabel_number')
        ordering = ('employee__family', 'employee__name', 'employee__patronymic', 'position__name', 'department__name', 'rate', 'is_active')

    @staticmethod
    def get_lunch_duration(duration_by_employee: Union[int, None], position: str, duration_by_department: Union[int, None]):
        if duration_by_employee is not None:
            local_duration = duration_by_employee
        elif duration_by_department is not None:
            local_duration = duration_by_department
        else:
            local_duration = LUNCH_DURATION_BY_POSITIONS.get(position)
        return local_duration

    @staticmethod
    def employee_transfer(employee_position_id: int, date: str):
        employee_position: EmployeePosition = EmployeePosition.objects.filter(pk=employee_position_id).first()
        if not employee_position:
            return {"ok": False, "message": "Такого работника нет"}
        employee_position.date_transfer = date
        employee_position.save()
        return {"ok": True, "message": ""}

    @staticmethod
    def checking_blocked_date(date: str, date_dismissal: Optional[datetime.date], date_transfer: Optional[datetime.date]) -> bool:
        current_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        other_dates = [date_dismissal, date_transfer]
        return any(current_date >= day for day in other_dates if day)

    @staticmethod
    def get_by_ids(employee_position_ids: set):
        employee_positions = EmployeePosition.objects.filter(pk__in=employee_position_ids)
        return employee_positions

    @staticmethod
    def edit_lunch(employee_position_id: int, lunch_duration_in_minutes: int):
        employee_position = EmployeePosition.objects.filter(pk=employee_position_id).first()
        employee_position.lunch_duration = lunch_duration_in_minutes
        employee_position.save()

    @staticmethod
    def find_by_tabel_number(organization_id: int, tabel_number: str, active=True):
        employee_position = EmployeePosition.objects.filter(employee__hospital_id=organization_id, is_active=active, tabel_number=tabel_number).select_related("employee").first()
        return employee_position

    @staticmethod
    def can_delete(employee_position_id: int):
        if EmployeeWorkingHoursSchedule.objects.filter(employee_position_id=employee_position_id).exists():
            return False, "Невозможно удалить: есть записи в графике рабочего времени"
        if FactTimeWork.objects.filter(employee_position_id=employee_position_id).exists():
            return False, "Невозможно удалить: есть записи в табеле рабочего времени"
        return True, ""

    @staticmethod
    def remove(hospital_id: int, employee_position_id: int, who_deleted):
        employee_position = EmployeePosition.objects.filter(id=employee_position_id, employee__hospital_id=hospital_id).first()
        if not employee_position:
            raise ValueError("Должность сотрудника не найдена")

        can_delete, message = EmployeePosition.can_delete(employee_position_id)
        if not can_delete:
            raise ValueError(message)

        position_json = employee_position.json
        employee_position.delete()
        Log.log(employee_position_id, 121107, who_deleted, position_json)
        return position_json


class WorkDayStatus(models.Model):
    title = models.CharField(max_length=255, verbose_name='Наименование')
    short_title = models.CharField(max_length=25, verbose_name='Сокращенное наименование')
    hide = models.BooleanField(default=False, db_index=True)
    vacation_title = models.CharField(max_length=255, null=True, help_text="Доп. название для поиска в отпусках, 'ежегодный, основной'")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Статус времени для рабочей даты'
        verbose_name_plural = 'Статусы времени для рабочих дат'

    @staticmethod
    def get_workday_statuses(short=True):
        result = [{"id": status.pk, "label": status.short_title if short else status.title} for status in WorkDayStatus.objects.filter(hide=False)]
        return result

    @staticmethod
    def get_statuses_dict(full_title: bool = False):
        result = {status.id: status.title if full_title else status.short_title for status in WorkDayStatus.objects.filter(hide=False)}
        return result


class TimeTrackingDocument(models.Model):
    create_at = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Время создания")
    month = models.DateField(help_text="Месяц учета", db_index=True, default=None, blank=True, null=True)
    department = models.ForeignKey(Department, null=True, blank=True, default=None, db_index=True, on_delete=models.SET_NULL)
    doc_create = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True, help_text="Профиль автора", on_delete=models.SET_NULL)
    blocked = models.DateField(default=None, null=True, help_text="2025-05-21", verbose_name="День блокировки графика")

    class Meta:
        verbose_name = "График-документ"
        verbose_name_plural = "График-документы"

    @staticmethod
    def create_document(year, month, department_id, doc_profile):
        month_date = datetime.date(year, month, 1)

        document = TimeTrackingDocument(
            doc_create_id=doc_profile.pk,
            create_at=timezone.now(),
            month=month_date,
            department_id=department_id,
        )
        document.save()
        EmployeeVacation.create_day_off_for_document(document)
        return document

    @staticmethod
    def check_document(document):
        current_day = current_time(True)
        if not document:
            return {"ok": False, "message": "Такого документа нет"}
        if document.blocked and current_day >= document.blocked:
            return {"ok": False, "message": "Документ заблокирован"}
        return {"ok": True, "message": ""}

    @staticmethod
    def get_document(first_date: datetime.date, last_date: datetime.date, department_id: int):
        document = TimeTrackingDocument.objects.filter(month__gte=first_date, month__lte=last_date, department_id=department_id).last()
        return document

    @staticmethod
    def get_document_for_print(document_id: int):
        document = TimeTrackingDocument.objects.filter(pk=document_id).select_related('department').first()
        return document


class TypeCheckTimeTrackingDocument(models.Model):
    title = models.CharField(max_length=255, verbose_name='Наименование')
    hide = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Статус проверки графика рабочего времени'
        verbose_name_plural = 'Статусы проверки графика рабочего времени'


class TimeTrackingStatus(models.Model):
    """
    raw_data = [
        {
            "snils": "121212121",
            "personLastname": "sds",
            "personFirstName": "sds",
            "personPatronymic": "sds",
            "employeeData": [
                {
                    "postTitle": "postTitle",
                    "typePost": "typePost",
                    "departmentTitle": "departmentTitle",
                    "tabelNumber": "tabelNumber",
                    "dates": [{"data": "20240229", "startTime": "0800", "endTime": "1600", "statusId": "1", "statusTitle": "работал"}],
                    "commonHours": {}
                },
            ]
        }
    ]
    """

    time_tracking_document = models.ForeignKey(TimeTrackingDocument, null=True, blank=True, default=None, db_index=True, on_delete=models.SET_NULL)
    doc_confirm = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True, help_text="Профиль автора", on_delete=models.SET_NULL)
    doc_confirm_string = models.CharField(max_length=64, null=True, blank=True, default=None)
    is_actual = models.BooleanField(help_text="Акутальный", default=True)
    version = models.PositiveSmallIntegerField(default=None, db_index=True, blank=True, null=True)
    comment_checking = models.TextField(blank=True, null=True, help_text="Комментарий от проверяющего")
    status = models.ForeignKey(TypeCheckTimeTrackingDocument, null=True, blank=True, default=None, db_index=True, on_delete=models.SET_NULL)
    doc_change_status = models.ForeignKey(DoctorProfile, related_name="doc_change_status", null=True, blank=True, db_index=True, help_text="Профиль проверяющего", on_delete=models.SET_NULL)
    doc_change_status_string = models.CharField(max_length=64, null=True, blank=True, default=None)
    time_change_status = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Время изменения статуса")
    raw_data = models.TextField(blank=True, null=True, help_text="Данные документа")

    class Meta:
        verbose_name = "График-документ-сохраненный"
        verbose_name_plural = "График-документы-сохраненный"


class EmployeeWorkingHoursSchedule(models.Model):
    time_tracking_document = models.ForeignKey(TimeTrackingDocument, null=True, blank=True, default=None, db_index=True, on_delete=models.SET_NULL)
    employee_position = models.ForeignKey(EmployeePosition, null=True, blank=True, db_index=True, default=None, on_delete=models.SET_NULL)
    start = models.DateTimeField(verbose_name='Начало рабочего времени', help_text='дата-время начала', null=True, blank=True)
    end = models.DateTimeField(verbose_name='Конец рабочего времени', help_text='дата-время окончания', null=True, blank=True)
    day = models.DateField(verbose_name='Дата учета времени', null=True, blank=True, default=None, db_index=True, help_text='дата')
    work_day_status = models.ForeignKey(WorkDayStatus, null=True, blank=True, default=None, db_index=True, on_delete=models.SET_NULL, verbose_name='Тип')
    user_saved = models.ForeignKey('users.DoctorProfile', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Профиль пользователя сохранившего запись')

    class Meta:
        verbose_name = "Сотрудник - фактическое время за дату"
        verbose_name_plural = "Сотрудники - фактическое время за дату"

    def __str__(self):
        employee = self.employee_position.employee if self.employee_position else None
        return f'{employee} {self.start} - {self.end}'

    @staticmethod
    def get_month_days_template(year: int, month: int, length_month: int):
        template_days = {
            datetime.date(year, month, day).strftime('%Y-%m-%d'): {"startWorkTime": None, "endWorkTime": None, "typeId": None, "blocked": False} for day in range(1, length_month + 1)
        }
        return template_days

    @staticmethod
    def get_work_time_employee(year: int, month: int, department_id: int):
        first_date_month = datetime.date(year, month, 1)
        length_month = calendar.monthrange(year, month)[1]
        last_date_month = datetime.date(year, month, length_month)
        document: TimeTrackingDocument = TimeTrackingDocument.get_document(first_date_month, last_date_month, department_id)
        result = []
        document_blocked = False
        document_created = True if document else False
        if document_created:
            template_days = EmployeeWorkingHoursSchedule.get_month_days_template(year, month, length_month)
            employees_work_time = get_employee_work_time(department_id, document.pk, str(first_date_month))
            result = {}
            for work_time in employees_work_time:
                if not result.get(work_time.employee_position_id):
                    result[work_time.employee_position_id] = {
                        "employeePositionId": work_time.employee_position_id,
                        "fio": f'{work_time.family} {work_time.name[0]}.{work_time.patronymic[0] + "." if work_time.patronymic else ""}',
                        "tabelNumber": work_time.tabel_number or "",
                        "position": work_time.position_name,
                        "bidType": work_time.bid_name[:3] if work_time.bid_name else "",
                        "lunchDuration": EmployeePosition.get_lunch_duration(work_time.lunch_duration, work_time.position_name, work_time.lunch_duration_by_department),
                    }
                    if work_time.date_dismissal or work_time.date_transfer:
                        result[work_time.employee_position_id].update(
                            {
                                date: {**values, "blocked": EmployeePosition.checking_blocked_date(date, work_time.date_dismissal, work_time.date_transfer)}
                                for date, values in template_days.items()
                            }
                        )
                    else:
                        result[work_time.employee_position_id].update({date: {**values} for date, values in template_days.items()})
                if work_time.day:
                    tmp_work_time = {
                        "startWorkTime": work_time.start_work.astimezone(pytz.timezone(TIME_ZONE)).strftime('%H:%M') if work_time.start_work else None,
                        "endWorkTime": work_time.end_work.astimezone(pytz.timezone(TIME_ZONE)).strftime('%H:%M') if work_time.end_work else None,
                        "typeId": work_time.work_day_status_id if work_time.work_day_status_id else None,
                    }
                    result[work_time.employee_position_id][work_time.day.strftime('%Y-%m-%d')].update(tmp_work_time)
            result = [value for value in result.values()]
            if document.blocked:
                document_blocked = current_time(True) >= document.blocked
        return {"data": result, "documentPk": document.pk if document else None, "documentIsBlocked": document_blocked, "documentIsCreated": document_created}

    @staticmethod
    def update_time(department_id: int, year: int, month: int, changed_time: dict):
        first_date_month = datetime.date(year, month, 1)
        length_month = calendar.monthrange(year, month)[1]
        last_date_month = datetime.date(year, month, length_month)
        document = TimeTrackingDocument.get_document(first_date_month, last_date_month, department_id)
        result_check = TimeTrackingDocument.check_document(document)
        if not result_check.get("ok"):
            return result_check

        desired = {}
        for position_id, date, work_time, _ in iter_changed_work_time_cells(changed_time):
            start, end = parse_schedule_start_end(date, work_time)
            desired[(position_id, date)] = {
                "start": start,
                "end": end,
                "work_day_status_id": normalize_work_day_status_id(work_time),
            }

        if not desired:
            return {"ok": True, "message": ""}

        position_ids = {position_id for position_id, _ in desired}
        days = {day for _, day in desired}
        existing = {
            (row.employee_position_id, row.day.strftime("%Y-%m-%d")): row
            for row in EmployeeWorkingHoursSchedule.objects.filter(time_tracking_document_id=document.pk, employee_position_id__in=position_ids, day__in=days)
        }

        to_create = []
        to_update = []
        for (position_id, date), values in desired.items():
            row = existing.get((position_id, date))
            if row:
                row.start = values["start"]
                row.end = values["end"]
                row.work_day_status_id = values["work_day_status_id"]
                to_update.append(row)
            else:
                to_create.append(
                    EmployeeWorkingHoursSchedule(
                        time_tracking_document_id=document.pk,
                        employee_position_id=position_id,
                        day=date,
                        start=values["start"],
                        end=values["end"],
                        work_day_status_id=values["work_day_status_id"],
                    )
                )

        if to_create:
            EmployeeWorkingHoursSchedule.objects.bulk_create(to_create)
        if to_update:
            EmployeeWorkingHoursSchedule.objects.bulk_update(to_update, ["start", "end", "work_day_status_id"])
        return {"ok": True, "message": ""}

    @staticmethod
    def fill_by_template(action: str, date_key: datetime.datetime, value, current_employee_position, lunch_duration_in_minutes, holidays):
        """
        Заполняет рабочие дни по шаблону работника.

        Рабочий день:
        - будний день вне holidays
        - или день с kind=WORKING (например, рабочая суббота)

        Не заполняет праздники (HOLIDAY) и обычные выходные.

        Заполняет если:
        - action == "replace"
        - action == "add" и текущее значение пустое

        Учитывает shorten_minutes (сокращает рабочий день).
        """
        value_is_empty = all(not value.get(key) for key in ['startWorkTime', 'endWorkTime', 'typeId'])
        is_valid_action = action == "replace" or (action == "add" and value_is_empty)
        if not is_valid_action:
            return value

        holiday_info: dict = holidays.get(date_key.strftime("%Y-%m-%d")) or {}
        holiday_kind = holiday_info.get("kind")
        shorten_minutes: Optional[int] = holiday_info.get("shorten_minutes") or 0

        if holiday_info:
            is_working_day = holiday_kind == Holidays.Kind.WORKING
        else:
            is_working_day = date_key.isoweekday() not in (6, 7)

        if not is_working_day:
            return value

        start_work_time_employee: datetime.time = current_employee_position.work_start
        daily_hours_norm_in_minutes: int = current_employee_position.daily_hours_norm or 0
        lunch_duration_in_minutes: int = lunch_duration_in_minutes or 0

        total_minutes: int = daily_hours_norm_in_minutes + lunch_duration_in_minutes - shorten_minutes
        total_minutes = max(total_minutes, 0)

        start_work_time_by_employee_template = datetime.datetime.combine(date_key.date(), start_work_time_employee)
        end_work_time_by_employee_template = start_work_time_by_employee_template + datetime.timedelta(minutes=total_minutes)

        result = {
            "startWorkTime": start_work_time_by_employee_template.strftime("%H:%M"),
            "endWorkTime": end_work_time_by_employee_template.strftime("%H:%M"),
            "typeId": None,
        }
        return result

    @staticmethod
    def get_work_time_filling_by_employee_template(year: int, month: int, department_id: int, action: str):
        employees_work_time = EmployeeWorkingHoursSchedule.get_work_time_employee(year, month, department_id)
        employee_position_ids = set()
        employees_work_time_data = employees_work_time.get("data")
        holidays = Holidays.get_holidays(datetime.date(year, month, 1))
        for employee_work_time in employees_work_time_data:
            employee_position_ids.add(employee_work_time.get("employeePositionId"))
        employee_positions_by_id = {employee_position.pk: employee_position for employee_position in EmployeePosition.get_by_ids(employee_position_ids)}
        for employee_work_time in employees_work_time_data:
            current_employee_position_id = employee_work_time.get("employeePositionId")
            lunch_duration = employee_work_time.get("lunchDuration")
            current_employee_position = employee_positions_by_id.get(current_employee_position_id)
            for key, value in employee_work_time.items():
                try:
                    date_key = datetime.datetime.strptime(key, "%Y-%m-%d")
                    new_value = EmployeeWorkingHoursSchedule.fill_by_template(action, date_key, value, current_employee_position, lunch_duration, holidays)
                    employee_work_time[key] = new_value
                except ValueError:
                    continue
        return employees_work_time_data


class EmployeeVacation(models.Model):
    employee_position = models.ForeignKey(EmployeePosition, null=True, db_index=True, on_delete=models.SET_NULL)
    start = models.DateField()
    end = models.DateField()
    work_day_status = models.ForeignKey(WorkDayStatus, null=True, on_delete=models.SET_NULL)
    hide = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Работник - отпуск"
        verbose_name_plural = "Работники - отпуска"

    def __str__(self):
        employee = self.employee_position.employee if self.employee_position else None
        return f'{employee} {self.start} - {self.end}'

    @staticmethod
    def create_day_off_for_document(time_tracking_document: TimeTrackingDocument):
        month = time_tracking_document.month
        department_id = time_tracking_document.department_id
        month_start = month.replace(day=1)
        month_end = month.replace(day=calendar.monthrange(month.year, month.month)[1])

        employee_positions = EmployeePosition.objects.filter(department_id=department_id, is_active=True)

        vacations = EmployeeVacation.objects.filter(
            employee_position__in=employee_positions,
            hide=False,
            start__lte=month_end,
            end__gte=month_start,
        ).select_related('employee_position', 'work_day_status')

        day_offs = []
        for vacation in vacations:
            start = max(vacation.start, month_start)
            end = min(vacation.end, month_end)
            days_count = (end - start).days + 1
            day_offs.extend(
                EmployeeWorkingHoursSchedule(
                    time_tracking_document=time_tracking_document,
                    employee_position=vacation.employee_position,
                    day=start + datetime.timedelta(days=offset),
                    work_day_status=vacation.work_day_status,
                )
                for offset in range(days_count)
            )
        EmployeeWorkingHoursSchedule.objects.bulk_create(day_offs, ignore_conflicts=True)


class CashRegister(models.Model):
    employee_position = models.ForeignKey(EmployeePosition, null=True, blank=True, db_index=True, default=None, on_delete=models.SET_NULL)
    accounting_day = models.DateField(verbose_name='Дата учета', null=True, blank=True, default=None, db_index=True, help_text='дата')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name='Отдел')
    received_terminal = models.DecimalField(max_digits=10, null=True, blank=True, default=None, decimal_places=2)
    received_cash = models.DecimalField(max_digits=10, null=True, blank=True, default=None, decimal_places=2)
    return_terminal = models.DecimalField(max_digits=10, null=True, blank=True, default=None, decimal_places=2)
    return_cash = models.DecimalField(max_digits=10, null=True, blank=True, default=None, decimal_places=2)

    def __str__(self):
        employee = self.employee_position.employee if self.employee_position else None
        return f'{employee} {self.accounting_day}'

    class Meta:
        verbose_name = "Сотрудник - учет финансов за день"
        verbose_name_plural = "Сотрудники - учет финансов за день"

    @staticmethod
    def get_cash_register_by_period(date_start, date_end):
        pass


class PlanDepartment(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name='Отдел')
    month = models.DateField(help_text="Месяц учета", db_index=True, default=None, blank=True, null=True)
    plan = models.DecimalField(max_digits=10, null=True, blank=True, default=None, decimal_places=2)

    def __str__(self):
        return f'{self.department.__str__()} {self.month}'

    class Meta:
        verbose_name = "Подразделение - план финансовый за месяц"
        verbose_name_plural = "Подразделения - план финансовый за месяц"


class EmployeePositionCountWorkDayPerMonth(models.Model):
    employee_position = models.ForeignKey(EmployeePosition, null=True, blank=True, db_index=True, default=None, on_delete=models.SET_NULL)
    count_work_day_per_month = models.PositiveSmallIntegerField(db_index=True, blank=True, null=True, default=None, help_text='Кол-во рабочих дней в месяц')
    month = models.DateField(help_text="Месяц учета", db_index=True, default=None, blank=True, null=True)
    plan_day_profit = models.DecimalField(max_digits=10, null=True, blank=True, default=None, decimal_places=2)

    def __str__(self):
        return f'{self.employee_position} {self.month} {self.count_work_day_per_month}'

    class Meta:
        verbose_name = "Сотрудник - план финансовый за день"
        verbose_name_plural = "Сотрудники - план финансовый за день"


class TabelDocument(models.Model):
    class Status(models.TextChoices):
        APPROVED = "APPROVED", "Утвержден"
        CHECK = "CHECK", "На проверке"
        TO_CORRECT = "TO_CORRECT", "Исправить"

    doc_confirmation = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True, help_text="Профиль автора", on_delete=models.SET_NULL)
    doc_confirmation_string = models.CharField(max_length=64, null=True, blank=True, default=None)
    time_confirmation = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Время подтверждения табеля")
    time_save = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Время сохранения табеля")
    month_tabel = models.DateField(help_text="Месяц учета", db_index=True)
    department = models.ForeignKey(Department, null=True, on_delete=models.SET_NULL)
    is_actual = models.BooleanField(help_text="Актуальный", default=True)
    version = models.PositiveSmallIntegerField(default=None, db_index=True, blank=True, null=True)
    parent_document = models.ForeignKey("self", related_name="parent_tabel_document", help_text="Документ основание", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    comment_checking = models.TextField(blank=True, null=True, help_text="Комментарий от проверяющего")
    status = models.CharField(max_length=20, null=True, blank=True, default=Status.CHECK, db_index=True, choices=Status.choices, help_text="Статус")
    doc_change_status = models.ForeignKey(
        DoctorProfile, related_name="tabel_doc_change_status", null=True, blank=True, db_index=True, help_text="Профиль проверяющего", on_delete=models.SET_NULL
    )
    doc_change_status_string = models.CharField(max_length=64, null=True, blank=True, default=None)
    time_change_status = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Время изменения статуса")

    class Meta:
        verbose_name = "Табель"
        verbose_name_plural = "Табели"

    def __str__(self):
        month_text = date_format(self.month_tabel, "F Y")
        department_text = self.department.name if self.department else "—"
        status_text = self.get_status_display()
        return f"{month_text} — {department_text} — {status_text}"

    @staticmethod
    def create_tabel_document(data, docprofile):
        month_tabel = try_strptime(data["dateTabel"]).date()
        department_pk = data["departmentPk"]
        version = 1
        parent_document = None
        if data.get("parentDocumentPk", None):
            parent_document = TabelDocument.objects.get(pk=data["parentDocumentPk"])
            version = parent_document.version + 1

        td = TabelDocument(
            doc_confirmation=docprofile,
            doc_confirmation_string=docprofile.get_full_fio(),
            time_save=timezone.now(),
            month_tabel=month_tabel,
            department_id=department_pk,
            is_actual=True,
            parent_document_id=data.get("parentDocumentPk", None),
            version=version,
        )
        if data.get("withConfirm", None):
            td.time_confirmation = timezone.now()
            td.status = "STATUS_CHECK"
            if parent_document:
                parent_document.is_actual = False
                parent_document.save()

        td.save()

    @staticmethod
    def change_status_tabel_document(tabel_pk, data, doc_profile):
        td = TabelDocument.objects.get(pk=tabel_pk)
        td.doc_change_status = doc_profile
        td.doc_change_status_string = doc_profile.get_full_fio()
        td.time_change_status = timezone.now()
        td.comment_checking = data.get("commentChecking", "")
        td.status = data.get("status", "")
        td.save()

    @staticmethod
    def get_or_create_tabel(first_date_month: datetime.date, last_date_month: datetime.date, department_id: int):
        tabel_document = TabelDocument.objects.filter(month_tabel__gte=first_date_month, month_tabel__lte=last_date_month, department_id=department_id, is_actual=True).first()
        if not tabel_document:
            tabel_document = TabelDocument.objects.create(month_tabel=first_date_month, department_id=department_id, is_actual=True)
        return tabel_document


class FactTimeWork(models.Model):
    tabel_document = models.ForeignKey(TabelDocument, null=True, on_delete=models.SET_NULL)
    employee_position = models.ForeignKey(EmployeePosition, null=True, on_delete=models.SET_NULL)
    date = models.DateField(help_text="Дата учета", db_index=True)
    night_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    common_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    work_day_status = models.ForeignKey(WorkDayStatus, null=True, blank=True, default=None, db_index=True, on_delete=models.SET_NULL, verbose_name='Тип')

    class Meta:
        verbose_name = "Время в табеле"
        verbose_name_plural = "Время в табеле"

    @staticmethod
    def overlap(start1: datetime.datetime, end1: datetime.datetime, start2: datetime.datetime, end2: datetime.datetime) -> datetime.timedelta:
        """Возвращает пересечение двух интервалов"""
        start = max(start1, start2)
        end = min(end1, end2)
        return max(end - start, datetime.timedelta(0))

    @staticmethod
    def calculate_day_night_hours(start_work: datetime.datetime, end_work: datetime.datetime):
        total_duration = end_work - start_work

        day = start_work.date()
        tz = start_work.tzinfo

        night_intervals = [
            (
                datetime.datetime.combine(day, datetime.time(0, 0), tz),
                datetime.datetime.combine(day, datetime.time(4, 0), tz),
            ),
            (
                datetime.datetime.combine(day, datetime.time(22, 0), tz),
                datetime.datetime.combine(day, datetime.time(23, 59, 59), tz) + datetime.timedelta(seconds=1),
            ),
        ]
        night_duration = datetime.timedelta(0)
        for night_start, night_end in night_intervals:
            night_duration += FactTimeWork.overlap(start_work, end_work, night_start, night_end)

        day_duration = total_duration - night_duration

        day_hours = round(day_duration.total_seconds() / 3600, 2)
        night_hours = round(night_duration.total_seconds() / 3600, 2)

        return {"day_hours": day_hours, "night_hours": night_hours}

    @staticmethod
    def update_time(department_id: int, year: int, month: int, changed_time: dict):
        first_date_month = datetime.date(year, month, 1)
        length_month = calendar.monthrange(year, month)[1]
        last_date_month = datetime.date(year, month, length_month)
        tabel_document: TabelDocument = TabelDocument.get_or_create_tabel(first_date_month, last_date_month, department_id)

        desired = {}
        for position_id, date, work_time, lunch_duration in iter_changed_work_time_cells(changed_time):
            day_hours = None
            night_hours = None
            start, end = parse_fact_start_end_datetimes(date, work_time)
            if start and end:
                hours = FactTimeWork.calculate_day_night_hours(start, end)
                day_hours = hours.get("day_hours")
                if lunch_duration:
                    day_hours = max(day_hours - lunch_duration / 60, 0)
                night_hours = hours.get("night_hours")
            desired[(position_id, date)] = {
                "common_hours": day_hours,
                "night_hours": night_hours,
                "work_day_status_id": normalize_work_day_status_id(work_time),
            }

        if not desired:
            return

        position_ids = {position_id for position_id, _ in desired}
        days = {day for _, day in desired}
        existing = {
            (row.employee_position_id, row.date.strftime("%Y-%m-%d")): row
            for row in FactTimeWork.objects.filter(tabel_document_id=tabel_document.pk, employee_position_id__in=position_ids, date__in=days)
        }

        to_create = []
        to_update = []
        for (position_id, date), values in desired.items():
            row = existing.get((position_id, date))
            if row:
                row.common_hours = values["common_hours"]
                row.night_hours = values["night_hours"]
                row.work_day_status_id = values["work_day_status_id"]
                to_update.append(row)
            else:
                to_create.append(
                    FactTimeWork(
                        tabel_document_id=tabel_document.pk,
                        employee_position_id=position_id,
                        date=date,
                        common_hours=values["common_hours"],
                        night_hours=values["night_hours"],
                        work_day_status_id=values["work_day_status_id"],
                    )
                )

        if to_create:
            FactTimeWork.objects.bulk_create(to_create)
        if to_update:
            FactTimeWork.objects.bulk_update(to_update, ["common_hours", "night_hours", "work_day_status_id"])

    @staticmethod
    def get_month_days_template(year: int, month: int, length_month: int):
        template_days = {datetime.date(year, month, day).strftime('%Y-%m-%d'): {"day_hours": "", "night_hours": "", "typeId": None} for day in range(1, length_month + 1)}
        return template_days

    @staticmethod
    def get_fact_time_work_employee(year: int, month: int, department_id: int):
        first_date_month = datetime.date(year, month, 1)
        length_month = calendar.monthrange(year, month)[1]
        last_date_month = datetime.date(year, month, length_month)
        tabel_document: TabelDocument = TabelDocument.get_or_create_tabel(first_date_month, last_date_month, department_id)

        template_days = FactTimeWork.get_month_days_template(year, month, length_month)
        employee_fact_time_work = get_employee_fact_time_work(department_id, tabel_document.pk, str(first_date_month))
        grouped_result = {}

        for fact_work_time in employee_fact_time_work:
            if not grouped_result.get(fact_work_time.employee_position_id):
                grouped_result[fact_work_time.employee_position_id] = {
                    "employee_positon_id": fact_work_time.employee_position_id,
                    "fio": make_short_name_form(fact_work_time.family, fact_work_time.name, fact_work_time.patronymic, True, True),
                    "position_name": fact_work_time.position_name,
                    "bid_type": fact_work_time.bid_name[:3] if fact_work_time.bid_name else "",
                    "tabel_number": fact_work_time.tabel_number,
                    "rate": fact_work_time.rate,
                    "day_hours_sum": 0,
                    "night_hours_sum": 0,
                    "common_hours_sum": 0,
                }
                grouped_result[fact_work_time.employee_position_id].update(copy.deepcopy(template_days))
            if fact_work_time.date:
                day_hours = fact_work_time.day_hours if fact_work_time.day_hours else None
                night_hours = fact_work_time.night_hours if fact_work_time.night_hours else None
                type_id = fact_work_time.work_day_status_id if fact_work_time.work_day_status_id else None
                tmp_work_time = {
                    "day_hours": day_hours,
                    "night_hours": night_hours,
                    "type_id": type_id,
                }
                grouped_result[fact_work_time.employee_position_id][fact_work_time.date.strftime('%Y-%m-%d')].update(tmp_work_time)
                if day_hours:
                    grouped_result[fact_work_time.employee_position_id]["day_hours_sum"] += day_hours
                    grouped_result[fact_work_time.employee_position_id]["common_hours_sum"] += day_hours
                if night_hours:
                    grouped_result[fact_work_time.employee_position_id]["night_hours_sum"] += night_hours
                    grouped_result[fact_work_time.employee_position_id]["common_hours_sum"] += night_hours

        result = [value for value in grouped_result.values()]
        return {"result": result, "document": tabel_document}


class TabelFactTimeWorkRaw(models.Model):
    """
    data_document = {"tabelDocumentPk": "", "personData": [
                            {
                                "snils": "121212121",
                                "person_family": "sds",
                                "person_name": "sds",
                                "person_patronymic": "sds",
                                "work_hours": [
                                    {
                                        "position_name": "postTitle",
                                        "bid_name": "bid_name",
                                        "department_name": "department_name",
                                        "tabel_number": "tabel_number",
                                        "days": {"2026-02-01": {"work_day_status": "", "nightHours": 4, "common_hours": 4}}
                                    },
                                    {
                                        "position_name": "other_post_title",
                                        "bid_name": "other_bid_name",
                                        "department_name": "other_department_name",
                                        "tabel_number": "other_tabel_number",
                                        "days": {"2026-02-02": {"work_day_status": "Отпуск", "nightHours": None, "common_hours": None}}
                                    }
                                ]
                            },
                        ]
                    }
    """

    tabel_document = models.ForeignKey(TabelDocument, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    data_document = models.TextField(blank=True, null=True, help_text="Данные документа")
    data_document_hash = models.CharField(max_length=64, null=True)

    class Meta:
        verbose_name = "Табель документ"
        verbose_name_plural = "Табель документы"

    @staticmethod
    def save_fact_time_work_document(tabel_pk, data_document):
        if tabel_pk > -1:
            document_fact_time = TabelFactTimeWorkRaw.objects.get(pk=tabel_pk)
            document_fact_time.data_document = data_document
            document_fact_time.save()

    @staticmethod
    def get_fact_time_work_document(tabel_pk):
        data = ""
        result = {}
        if tabel_pk > -1:
            document_fact_time = TabelFactTimeWorkRaw.objects.get(pk=tabel_pk)
            data = json.loads(document_fact_time)
            for person in data.get("personData") or []:
                for employeee in person.get("employeeData") or []:
                    tmp_dates = sorted(employeee.get("dates", []).copy())
                    result[person][employeee]["tmp_night_hours_dates"] = ["" for i in range(len(tmp_dates))]
                    result[person][employeee]["tmp_night_hours"] = employeee.get("nightHours", {})
                    result[person][employeee]["tmp_common_hours"] = employeee.get("commonHours", {})

        return result


class Holidays(models.Model):
    class Kind(models.TextChoices):
        HOLIDAY = "HOLIDAY", "Праздничный день"
        WORKING = "WORKING", "Рабочий день"

    day = models.DateField()
    kind = models.CharField(max_length=20, db_index=True, default=Kind.HOLIDAY, choices=Kind.choices, help_text="Тип")
    shorten_minutes = models.PositiveSmallIntegerField(default=0, help_text="Сокращение рабочего времени, минуты")

    def __str__(self):
        return f"{self.day}"

    class Meta:
        verbose_name = "Праздничный день"
        verbose_name_plural = "Праздничные дни"

    @staticmethod
    def get_holidays(month: datetime.date = None, year: int = None):
        holidays = Holidays.objects.all().order_by("day")
        if month:
            first_date_month = month.replace(day=1)
            last_day_month = calendar.monthrange(month.year, month.month)[1]
            end_date_month = month.replace(day=last_day_month)
            holidays = holidays.filter(day__range=(first_date_month, end_date_month))
        elif year:
            holidays = holidays.filter(day__year=year)

        result = {
            holiday.day.strftime("%Y-%m-%d"): {"kind": holiday.kind, "shorten_minutes": None if holiday.kind == Holidays.Kind.HOLIDAY else holiday.shorten_minutes} for holiday in holidays
        }
        return result


class DoctorProfileDepartment(models.Model):
    doctor_profile = models.ForeignKey(DoctorProfile, db_index=True, null=True, on_delete=models.SET_NULL)
    department = models.ForeignKey(Department, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.doctor_profile} - {self.department_id}"

    class Meta:
        verbose_name = "Разрешенное подразделение"
        verbose_name_plural = "Разрешенные подразделения"

    @staticmethod
    def save_doctor_departments(doctor_profile: DoctorProfile, allowed_department_ids: list):
        new_ids = set(allowed_department_ids)
        current_ids = set(DoctorProfileDepartment.objects.filter(doctor_profile_id=doctor_profile.id).values_list("department_id", flat=True))

        ids_to_delete = current_ids - new_ids
        ids_to_create = new_ids - current_ids

        if ids_to_delete:
            DoctorProfileDepartment.objects.filter(
                doctor_profile=doctor_profile,
                department_id__in=ids_to_delete,
            ).delete()

        if ids_to_create:
            DoctorProfileDepartment.objects.bulk_create(
                [
                    DoctorProfileDepartment(
                        doctor_profile=doctor_profile,
                        department_id=department_id,
                    )
                    for department_id in ids_to_create
                ]
            )

    @staticmethod
    def get_doctor_departments_ids(doctor_profile: DoctorProfile):
        result = DoctorProfileDepartment.objects.filter(doctor_profile_id=doctor_profile.id).values_list("department_id", flat=True)
        return list(result)
