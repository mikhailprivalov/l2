import calendar
import datetime

from django.db import models
from django.core.paginator import Paginator

from employees.sql_func import get_employees_by_department, get_work_time_by_document
from hospitals.models import Hospitals
from laboratory.utils import strfdatetime
from slog.models import Log
from users.models import DoctorProfile
from utils.dates import try_strptime
from django.utils import timezone


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
        departments = [{"id": department.pk, "label": department.name} for department in Department.objects.filter(is_active=True, hospital_id=hospital_id).order_by('name')]
        return departments

    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'
        indexes = [
            models.Index(fields=['hospital', 'name', 'is_active']),
        ]
        unique_together = ('hospital', 'name')
        ordering = ('hospital__short_title', 'hospital__title', 'name')


class TypeWorkTimeEmployee(models.Model):
    title = models.CharField(max_length=255, help_text='Занятость (осн | внутр.свом| внеш. совм)')

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = 'Тип занятости'
        verbose_name_plural = 'Типы занятости'


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


class WorkDayStatus(models.Model):
    title = models.CharField(max_length=255, verbose_name='Наименование')
    short_title = models.CharField(max_length=25, verbose_name='Сокращенное наименование')
    hide = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Статус времени для рабочей даты'
        verbose_name_plural = 'Статусы времени для рабочих дат'


class TimeTrackingDocument(models.Model):
    create_at = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Время создания")
    month = models.DateField(help_text="Месяц учета", db_index=True, default=None, blank=True, null=True)
    department = models.ForeignKey(Department, null=True, blank=True, default=None, db_index=True, on_delete=models.SET_NULL)
    doc_create = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True, help_text="Профиль автора", on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "График-документ"
        verbose_name_plural = "График-документы"

    @staticmethod
    def create_time_tracking_document(data, docprofile):
        month = try_strptime(data["date"]).date()
        department_pk = data["departmentPk"]

        TimeTrackingDocument(
            doc_confirmation=docprofile,
            doc_confirmation_string=docprofile.get_full_fio(),
            time_save=timezone.now(),
            month_tabel=month,
            department_id=department_pk,
        ).save()


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
        verbose_name = "График-документ"
        verbose_name_plural = "График-документы"


class EmployeeWorkingHoursSchedule(models.Model):
    time_tracking_document = models.ForeignKey(TimeTrackingDocument, null=True, blank=True, default=None, db_index=True, on_delete=models.SET_NULL)
    employee_position = models.ForeignKey(EmployeePosition, null=True, blank=True, db_index=True, default=None, on_delete=models.SET_NULL)
    start = models.DateTimeField(verbose_name='Начало рабочего времени', help_text='дата-время начала')
    end = models.DateTimeField(verbose_name='Конец рабочего времени', help_text='дата-время окончания')
    day = models.DateField(verbose_name='Дата учета времени', null=True, blank=True, default=None, db_index=True, help_text='дата')
    work_day_status = models.ForeignKey(WorkDayStatus, null=True, blank=True, default=None, db_index=True, on_delete=models.SET_NULL, verbose_name='Тип')
    user_saved = models.ForeignKey('users.DoctorProfile', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Профиль пользователя сохранившего запись')

    def __str__(self):
        return f'{self.employee_position.employee.__str__()} {self.start} - {self.end}'

    @staticmethod
    def get_employees_template(year: int, month: int, last_date_month: int, department_id: int):
        template_days = {datetime.date(year, month, day).strftime('%Y-%m-%d'): {"startWorkTime": "", "endWorkTime": "", "type": ""} for day in range(1, last_date_month + 1)}
        employees = get_employees_by_department(department_id)
        employees_template = {}
        for employee in employees:
            employees_template[employee.employee_position_id] = template_days.copy()
            employees_template[employee.employee_position_id] = {
                "fio": f'{employee.family} {employee.name[0]}.{employee.patronymic[0] + "." if employee.patronymic else ""}',
                "position": employee.position_name,
                "bidType": 'осн',
                "normMonth": '178',
                "normDay": "8",
            }
        return employees_template

    @staticmethod
    def get_work_time(year: int, month: int, department_id: int):
        first_date = datetime.date(year, month, 1)
        last_day_month = calendar.monthrange(year, month)[1]
        last_date_month = datetime.date(year, month, last_day_month)
        template_employee = EmployeeWorkingHoursSchedule.get_employees_template(year, month, last_day_month, department_id)
        document = TimeTrackingDocument.objects.filter(month__gte=first_date, month__lte=last_date_month, department_id=department_id).last()
        result = []
        if document:
            employees_work_time = get_work_time_by_document(document.pk)
            for time in employees_work_time:
                print('ура')
            result = [value for value in template_employee.values()]
        return result

    class Meta:
        verbose_name = "Сотрудник - фактическое время за дату"
        verbose_name_plural = "Сотрудники - фактическое время за дату"


class CashRegister(models.Model):
    employee_position = models.ForeignKey(EmployeePosition, null=True, blank=True, db_index=True, default=None, on_delete=models.SET_NULL)
    accounting_day = models.DateField(verbose_name='Дата учета', null=True, blank=True, default=None, db_index=True, help_text='дата')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name='Отдел')
    received_terminal = models.DecimalField(max_digits=10, null=True, blank=True, default=None, decimal_places=2)
    received_cash = models.DecimalField(max_digits=10, null=True, blank=True, default=None, decimal_places=2)
    return_terminal = models.DecimalField(max_digits=10, null=True, blank=True, default=None, decimal_places=2)
    return_cash = models.DecimalField(max_digits=10, null=True, blank=True, default=None, decimal_places=2)

    def __str__(self):
        return f'{self.employee_position.employee.__str__()} {self.accounting_day}'

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
        return f'{self.employee_position.__str__()} {self.month} {self.count_work_day_per_month}'

    class Meta:
        verbose_name = "Сотрудник - план финансовый за день"
        verbose_name_plural = "Сотрудники - план финансовый за день"
