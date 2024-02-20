import calendar
import datetime

import pytz
from django.db import models
from django.core.paginator import Paginator

from employees.sql_func import get_work_time_by_document, get_employees_by_department
from hospitals.models import Hospitals
from laboratory.settings import TIME_ZONE
from laboratory.utils import strfdatetime
from slog.models import Log


class Employee(models.Model):
    hospital = models.ForeignKey(Hospitals, on_delete=models.CASCADE, verbose_name='Медицинское учреждение')
    family = models.CharField(max_length=64, verbose_name='Фамилия')
    name = models.CharField(max_length=64, verbose_name='Имя')
    patronymic = models.CharField(max_length=64, verbose_name='Отчество')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    doctorprofile_created = models.ForeignKey(
        'users.DoctorProfile', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Профиль пользователя, создавшего запись', related_name='employees_employee_created'
    )
    doctorprofile_updated = models.ForeignKey(
        'users.DoctorProfile', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Профиль пользователя, обновившего запись', related_name='employees_employee_updated'
    )

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

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        indexes = [
            models.Index(fields=['hospital', 'family', 'name', 'patronymic', 'is_active']),
        ]
        unique_together = ('hospital', 'family', 'name', 'patronymic', 'is_active')
        ordering = ('hospital__short_title', 'hospital__title', 'family', 'name', 'patronymic')


class Position(models.Model):
    hospital = models.ForeignKey(Hospitals, on_delete=models.CASCADE, verbose_name='Медицинское учреждение')
    name = models.CharField(max_length=64, verbose_name='Название должности')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    doctorprofile_created = models.ForeignKey(
        'users.DoctorProfile', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Профиль пользователя, создавшего запись', related_name='employees_position_created'
    )
    doctorprofile_updated = models.ForeignKey(
        'users.DoctorProfile', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Профиль пользователя, обновившего запись', related_name='employees_position_updated'
    )

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

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'
        indexes = [
            models.Index(fields=['hospital', 'name', 'is_active']),
        ]
        unique_together = ('hospital', 'name')
        ordering = ('hospital__short_title', 'hospital__title', 'name')


class Department(models.Model):
    hospital = models.ForeignKey(Hospitals, on_delete=models.CASCADE, verbose_name='Медицинское учреждение')
    name = models.CharField(max_length=64, verbose_name='Название отдела')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    doctorprofile_created = models.ForeignKey(
        'users.DoctorProfile', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Профиль пользователя, создавшего запись', related_name='employees_department_created'
    )
    doctorprofile_updated = models.ForeignKey(
        'users.DoctorProfile', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Профиль пользователя, обновившего запись', related_name='employees_department_updated'
    )

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
    def get_active_labels(hospital_id: int = Hospitals.objects.get(is_default=True)):
        departments = [
            {
                "id": department.pk,
                "label": department.name
            }
            for department in Department.objects.filter(is_active=True, hospital_id=hospital_id).order_by('name')]
        return departments

    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'
        indexes = [
            models.Index(fields=['hospital', 'name', 'is_active']),
        ]
        unique_together = ('hospital', 'name')
        ordering = ('hospital__short_title', 'hospital__title', 'name')


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
    def add(hospital_id, employee_id, position_id, department_id, rate, who_created):
        EmployeePosition.validate_values(employee_id, position_id, department_id, rate)
        position = Position.objects.get(id=position_id, hospital_id=hospital_id)
        department = Department.objects.get(id=department_id, hospital_id=hospital_id)
        employee_position = EmployeePosition(employee_id=employee_id, position=position, department=department, rate=rate, doctorprofile_created=who_created)
        employee_position.save()
        Log.log(employee_position.pk, 121106, who_created, employee_position.json)
        return employee_position.json

    @staticmethod
    def edit(hospital_id, employee_position_id, position_id, department_id, rate, is_active, who_updated):
        employee_position = EmployeePosition.objects.get(id=employee_position_id, employee__hospital_id=hospital_id)
        EmployeePosition.validate_values(employee_position.employee_id, position_id, department_id, rate, current_id=employee_position_id)
        position = Position.objects.get(id=position_id, hospital_id=hospital_id)
        department = Department.objects.get(id=department_id, hospital_id=hospital_id)
        employee_position.position = position
        employee_position.department = department
        employee_position.rate = rate
        employee_position.is_active = is_active
        employee_position.doctorprofile_updated = who_updated
        employee_position.save()
        Log.log(employee_position.pk, 121107, who_updated, employee_position.json)
        return employee_position.json

    @staticmethod
    def validate_values(employee_id, position_id, department_id, rate, current_id=None):
        if current_id:
            employee_position = EmployeePosition.objects.filter(employee_id=employee_id, position_id=position_id, department_id=department_id).exclude(id=current_id)
        else:
            employee_position = EmployeePosition.objects.filter(employee_id=employee_id, position_id=position_id, department_id=department_id)
        if employee_position.exists():
            raise ValueError('Такая должность уже существует')
        if rate < 0:
            raise ValueError('Ставка не может быть отрицательной')

    class Meta:
        verbose_name = 'Должность сотрудника'
        verbose_name_plural = 'Должности сотрудников'
        indexes = [
            models.Index(fields=['employee', 'position', 'department', 'rate', 'is_active']),
        ]
        unique_together = ('employee', 'position', 'department', 'is_active')
        ordering = ('employee__family', 'employee__name', 'employee__patronymic', 'position__name', 'department__name', 'rate', 'is_active')


class WorkTimeDocument(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name='Подразделение', help_text='Отдел АСУ, Травмпункт и т.д')
    month = models.DateField(verbose_name='Месяц', help_text='Дата в месяце, (01.12.24)')

    def __str__(self):
        return f'{self.department} - {self.month}'

    @staticmethod
    def get_document(year: int, month: int, department: int):
        month_date = datetime.date(year, month, 1)
        document = WorkTimeDocument.objects.filter(department_id=department, month=month_date).first()
        if document:
            return document.pk
        return document

    @staticmethod
    def create_document(year: int, month: int, department: int):
        month_date = datetime.date(year, month, 1)
        document = WorkTimeDocument.objects.filter(department_id=department, month=month_date).first()
        if not document:
            document = WorkTimeDocument(department_id=department, month=month_date)
            document.save()
        return True

    class Meta:
        verbose_name = 'График рабочего времени'
        verbose_name_plural = 'Графики рабочего времени'
        indexes = [
            models.Index(fields=['department', 'month']),
        ]


class WorkTimeType(models.Model):
    title = models.CharField(max_length=255, verbose_name='Наименование')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Тип рабочего времени'
        verbose_name_plural = 'Типы рабочего времени'


class EmployeeWorkTime(models.Model):
    document = models.ForeignKey(WorkTimeDocument, on_delete=models.CASCADE, verbose_name='График')
    employee_position = models.ForeignKey(EmployeePosition, on_delete=models.CASCADE, verbose_name='Должность сотрудника')
    start = models.DateTimeField(verbose_name='Начало рабочего времени', help_text='03.01.2024 08:00')
    end = models.DateTimeField(verbose_name='Конец рабочего времени', help_text='03.01.2024 16:30')
    work_time_type = models.ForeignKey(WorkTimeType, default=None, on_delete=models.CASCADE, verbose_name='Тип')
    doctor_profile_saved = models.ForeignKey(
        'users.DoctorProfile', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Профиль пользователя сохранившего запись'
    )

    def __str__(self):
        return f'{self.employee_position.employee.__str__()}: {self.start} - {self.end}'

    @staticmethod
    def get_employees_template(document: WorkTimeDocument) -> dict:
        year, month = document.month.year, document.month.month
        _, end_month = calendar.monthrange(year, month)
        template_days = {datetime.date(year, month, day).strftime('%d.%m.%Y'): {"startWorkTime": "", "endWorkTime": "", "type": ""} for day in range(1, end_month + 1)}
        employees = get_employees_by_department(document.department_id)
        employees_template = {}
        for employee in employees:
            employees_template[employee.employee_position_id] = template_days.copy()
            employees_template[employee.employee_position_id]["fio"] = f'{employee.family} {employee.name[0]}.{employee.patronymic[0] + "." if employee.patronymic else ""}'
            employees_template[employee.employee_position_id]["position"] = employee.position_name
            employees_template[employee.employee_position_id]["bidType"] = 'осн'
            employees_template[employee.employee_position_id]["normMonth"] = '178'
            employees_template[employee.employee_position_id]["normDay"] = "8"
        return employees_template

    @staticmethod
    def get_work_time(document_id: int):
        document = WorkTimeDocument.objects.get(pk=document_id)
        employees_result = EmployeeWorkTime.get_employees_template(document)
        if not employees_result:
            return []
        employees_work_time = get_work_time_by_document(document.pk)
        for time in employees_work_time:
            work_time = employees_result[time.employee_position_id][time.start.strftime('%d.%m.%Y')].copy()
            work_time["startWorkTime"] = time.start.astimezone(pytz.timezone(TIME_ZONE)).strftime('%H:%M')
            work_time["endWorkTime"] = time.end.astimezone(pytz.timezone(TIME_ZONE)).strftime('%H:%M')
            employees_result[time.employee_position_id][time.start.strftime('%d.%m.%Y')] = work_time
        result = [
            value
            for _, value in employees_result.items()
        ]
        return result

    class Meta:
        verbose_name = 'Рабочее время сотрудника'
        verbose_name_plural = 'Рабочее время сотрудников'
        indexes = [
            models.Index(fields=['document', 'employee_position']),
        ]
