from typing import Any, Dict, Optional
from api.edit_forms.forms.base import BaseForm, FormObjectNotFoundException, HospitalObjectView
from api.edit_forms.forms.implementations.employee_employee import EmployeeEmployeeForm
from api.edit_forms.forms.implementations.employee_position import EmployeePositionForm
from employees.models import EmployeePosition, Department, TypeWorkTimeEmployee
from laboratory.utils import strfdatetime
from users.models import DoctorProfile


def _form_row(*fields):
    col_class = "col-xs-6" if len(fields) == 2 else "col-xs-4"
    return {
        "component": "div",
        "class": "row formulate-form-row",
        "children": [
            {"component": "div", "class": col_class, "children": [field]}
            for field in fields
        ],
    }


class EmployeeEmployeePositionForm(BaseForm, HospitalObjectView[EmployeePosition]):
    access_groups_to_edit = ('Конструктор: Настройка организации',)
    supports_delete = True
    model: EmployeePosition = EmployeePosition

    @staticmethod
    def _get_object_hospital_id(object: EmployeePosition) -> int:
        return object.department.hospital_id

    @staticmethod
    def _map_hospital_id_to_query(hospital_id: int) -> Dict[str, Any]:
        return dict(department__hospital_id=hospital_id)

    @classmethod
    def _default_rows(cls, doctorprofile: DoctorProfile):
        return cls.model.objects.all().prefetch_related('employee').prefetch_related('position')

    @staticmethod
    def _json(object: EmployeePosition) -> Optional[Dict[str, Any]]:
        employee_json = EmployeeEmployeeForm._json(object.employee)
        position_json = EmployeePositionForm._json(object.position)

        return {
            'id': object.id,
            'name': str(object),
            'employeeId': employee_json['id'],
            'employeeName': employee_json['fullName'],
            'positionName': position_json['name'],
            'positionId': position_json['id'],
            'departmentId': object.department_id,
            'rate': object.rate,
            'fullName': str(object),
            'isActive': object.is_active,
            'isActiveText': 'да' if object.is_active else 'нет',
            'createdAt': strfdatetime(object.created_at, "%d.%m.%Y %X"),
            'whoCreate': object.doctorprofile_created.get_fio() if object.doctorprofile_created else None,
            'updatedAt': strfdatetime(object.updated_at, "%d.%m.%Y %X") if object.updated_at else None,
            'whoUpdate': object.doctorprofile_updated.get_fio() if object.doctorprofile_updated else None,
        }

    @staticmethod
    def _search_filters(search: str):
        return [
            {
                "employee__family__istartswith": search,
            },
            {
                "employee__name__istartswith": search,
            },
            {
                "employee__patronymic__istartswith": search,
            },
            {
                "position__name__istartswith": search,
            },
            {
                "department__name__istartswith": search,
            },
        ]

    @staticmethod
    def _table_columns():
        return [
            {
                'field': 'employeeName',
                'key': 'employeeName',
                'title': 'ФИО',
                'align': "left",
            },
            {
                'field': 'positionName',
                'key': 'positionName',
                'title': 'Должность',
                'align': "left",
            },
            {
                'field': 'rate',
                'key': 'rate',
                'title': 'Ставка',
                'align': "right",
            },
            {
                'field': 'isActiveText',
                'key': 'isActiveText',
                'title': 'Активно',
                'align': "center",
            },
            {
                'key': 'edit',
            },
        ]

    @classmethod
    def get_form_data(cls, doctorprofile: DoctorProfile, form_data: Dict[str, Any]):
        hospital = cls.get_current_hospital(doctorprofile)
        employee_position_id = form_data.get('id')
        filters = form_data.get('filters') or {}
        employee_position: Optional[EmployeePosition] = None

        department_id = filters.get('department_id')

        if employee_position_id is not None:
            employee_position = cls.get_by_id(doctorprofile, employee_position_id)
            if not employee_position:
                raise FormObjectNotFoundException(f'Employee position with id {employee_position_id} not found')

        department = Department.get_by_id(cls.get_current_hospital_id(doctorprofile), department_id) if department_id else None

        if not department:
            raise FormObjectNotFoundException(f'Department id {department_id} not found')

        title = f"Редактирование должности сотрудника {cls._json(employee_position)['name']}" if employee_position else "Добавление новой должности сотрудника"

        type_work_time_options = [{"value": "", "label": "Не выбрано"}, *[{"value": item["id"], "label": item["label"]} for item in TypeWorkTimeEmployee.get_active()]]

        schema = [
            {"component": "h5", "children": f"Организация: {hospital.safe_short_title}"},
            {"component": "h6", "children": f"Подразделение: {department.name}"},
            _form_row(
                {"label": "Сотрудник", "validation-name": "Сотрудник", "name": "employeeId", "validation": "required", "type": "object-select", "formType": "employeeEmployee"},
                {"label": "Должность", "validation-name": "Должность", "name": "positionId", "validation": "required", "type": "object-select", "formType": "employeePosition"},
            ),
            _form_row(
                {"label": "Тип занятости", "validation-name": "Тип занятости", "name": "typeWorkTimeId", "type": "select", "options": type_work_time_options},
                {"label": "Время начала работы", "validation-name": "Время начала работы", "name": "workStart", "type": "time"},
            ),
            _form_row(
                {"label": "Ставка", "validation-name": "Ставка", "name": "rate", "validation": "required|number|between:0,3", "min": "0", "max": "3", "step": "0.01", "type": "number"},
                {"label": "Табельный номер", "validation-name": "Табельный номер", "name": "tabelNumber", "type": "text"},
                {"label": "Обед, мин", "validation-name": "Обед", "name": "lunchDuration", "type": "number", "min": "0", "step": "1"},
            ),
            _form_row(
                {"label": "Дата приема на работу", "validation-name": "Дата приема на работу", "name": "dateEmployment", "type": "date"},
                {"label": "Дата увольнения", "validation-name": "Дата увольнения", "name": "dateDismissal", "type": "date"},
                {"label": "Дата перевода", "validation-name": "Дата перевода", "name": "dateTransfer", "type": "date"},
            ),
            _form_row(
                {"label": "Дневная норма, мин", "validation-name": "Дневная норма", "name": "dailyHoursNorm", "type": "number", "min": "0", "step": "1"},
                {"label": "Недельная норма, мин", "validation-name": "Недельная норма", "name": "weeklyHoursNorm", "type": "number", "min": "0", "step": "1"},
                {"label": "Рабочих дней в неделю", "validation-name": "Рабочих дней в неделю", "name": "workDaysPerWeek", "type": "number", "min": "1", "max": "7", "step": "1"},
            ),
        ]

        if employee_position:
            schema.append(
                {
                    "label": "Должность сотрудника активна",
                    "name": "isActive",
                    "type": "checkbox",
                }
            )

        values = {
            "rate": employee_position.rate if employee_position else "1.0",
            "isActive": employee_position.is_active if employee_position else True,
            "employeeId": employee_position.employee_id if employee_position else None,
            "positionId": employee_position.position_id if employee_position else None,
            "tabelNumber": employee_position.tabel_number if employee_position else "",
            "typeWorkTimeId": employee_position.type_work_time_id if employee_position and employee_position.type_work_time_id else "",
            "dateEmployment": employee_position.date_employment.strftime("%Y-%m-%d") if employee_position and employee_position.date_employment else "",
            "dateDismissal": employee_position.date_dismissal.strftime("%Y-%m-%d") if employee_position and employee_position.date_dismissal else "",
            "dateTransfer": employee_position.date_transfer.strftime("%Y-%m-%d") if employee_position and employee_position.date_transfer else "",
            "lunchDuration": employee_position.lunch_duration if employee_position and employee_position.lunch_duration is not None else "",
            "dailyHoursNorm": employee_position.daily_hours_norm if employee_position and employee_position.daily_hours_norm is not None else "",
            "weeklyHoursNorm": employee_position.weekly_hours_norm if employee_position and employee_position.weekly_hours_norm is not None else "",
            "workDaysPerWeek": employee_position.work_days_per_week if employee_position and employee_position.work_days_per_week is not None else "",
            "workStart": employee_position.work_start.strftime("%H:%M") if employee_position and employee_position.work_start else "",
        }

        submit_text = "Сохранить изменения" if employee_position else "Добавить новую должность сотрудника"

        return {
            "title": title,
            "schema": schema,
            "values": values,
            "submitText": submit_text,
            "allowDelete": employee_position is not None,
        }

    @classmethod
    def delete(cls, doctorprofile: DoctorProfile, form_data: Dict[str, Any]):
        hospital_id = cls.get_current_hospital_id(doctorprofile)
        employee_position_id = form_data.get("id")

        if not employee_position_id:
            return {
                "ok": False,
                "message": "Не указана должность сотрудника для удаления",
                "result": {},
            }

        employee_position = cls.get_by_id(doctorprofile, employee_position_id)
        if not employee_position:
            raise FormObjectNotFoundException(f"Employee position with id {employee_position_id} not found")

        try:
            EmployeePosition.remove(hospital_id, employee_position_id, doctorprofile)
        except ValueError as e:
            return {
                "ok": False,
                "message": str(e),
                "result": {},
            }

        return {
            "ok": True,
            "message": f"Должность сотрудника \"{employee_position}\" успешно удалена",
            "result": {"id": employee_position_id, "deleted": True},
        }

    @classmethod
    def save(cls, doctorprofile: DoctorProfile, form_data: Dict[str, Any]):
        hospital_id = cls.get_current_hospital_id(doctorprofile)
        employee_position_id = form_data.get('id')
        form_values = form_data.get('values', {})
        employee_id = form_values.get('employeeId')
        position_id = form_values.get('positionId')
        rate = float(form_values.get('rate', -1))
        is_active = form_values.get('isActive', True)
        filters = form_data.get('filters') or {}

        department_id = filters.get('department_id')
        department: Department

        try:
            department = Department.get_by_id(cls.get_current_hospital_id(doctorprofile), department_id) if department_id else None

            if not department:
                raise FormObjectNotFoundException(f'Department id {department_id} not found')

            if employee_position_id is None:
                employee_position_json = EmployeePosition.add(hospital_id, employee_id, position_id, department_id, rate, doctorprofile, form_values)
            else:
                employee_position_json = EmployeePosition.edit(hospital_id, employee_position_id, position_id, department_id, rate, is_active, doctorprofile, form_values)
        except ValueError as e:
            return {
                "ok": False,
                "message": str(e),
                "result": {},
            }
        else:
            employee_position = cls.json(doctorprofile, cls.get_by_id(doctorprofile, employee_position_json["id"]))
            return {
                "ok": True,
                "message": f"Должность сотрудника \"{employee_position['fullName']}\" успешно сохранена",
                "result": employee_position,
            }
