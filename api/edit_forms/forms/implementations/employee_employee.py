from typing import Any, Dict, Optional
from api.edit_forms.forms.base import BaseForm, FormObjectNotFoundException, HospitalObjectView
from employees.models import Employee
from laboratory.utils import strfdatetime
from users.models import DoctorProfile


class EmployeeEmployeeForm(BaseForm, HospitalObjectView[Employee]):
    access_groups_to_edit = ('Конструктор: Настройка организации',)
    model: Employee = Employee

    @staticmethod
    def _json(object: Employee) -> Optional[Dict[str, Any]]:
        return {
            'id': object.id,
            'family': object.family,
            'name': object.name,
            'patronymic': object.patronymic,
            'fullName': f"{object.family} {object.name} {object.patronymic}".strip(),
            'isActive': object.is_active,
            'createdAt': strfdatetime(object.created_at, "%d.%m.%Y %X"),
            'whoCreate': object.doctorprofile_created.get_fio() if object.doctorprofile_created else None,
            'updatedAt': strfdatetime(object.updated_at, "%d.%m.%Y %X") if object.updated_at else None,
            'whoUpdate': object.doctorprofile_updated.get_fio() if object.doctorprofile_updated else None,
        }

    @staticmethod
    def list_name():
        return 'fullName'

    @staticmethod
    def _search_filters(search: str):
        return [
            {
                "family__istartswith": search,
            },
            {
                "name__istartswith": search,
            },
            {
                "patronymic__istartswith": search,
            },
        ]

    @classmethod
    def get_form_data(cls, doctorprofile: DoctorProfile, form_data: Dict[str, Any]):
        hospital = cls.get_current_hospital(doctorprofile)
        employee_id = form_data.get('id')
        employee = None

        if employee_id is not None:
            employee = cls.get_by_id(doctorprofile, employee_id)
            if not employee:
                raise FormObjectNotFoundException(f'Employee with id {employee_id} not found')

        title = f"Редактирование сотрудника {cls._json(employee)['fullName']}" if employee else "Добавление нового сотрудника"

        schema = [
            {"component": "h5", "children": f"Организация: {hospital.safe_short_title}"},
            {"label": "Фамилия", "validation-name": "Фамилия", "name": "family", "validation": "required:trim"},
            {"label": "Имя", "validation-name": "Имя", "name": "name", "validation": "required:trim"},
            {"label": "Отчество", "validation-name": "Отчество", "name": "patronymic", "validation": ""},
        ]

        if employee:
            schema.append(
                {
                    "label": "Сотрудник активен",
                    "name": "isActive",
                    "type": "checkbox",
                }
            )

        values = {
            "family": employee.family if employee else "",
            "name": employee.name if employee else "",
            "patronymic": employee.patronymic if employee else "",
            "isActive": employee.is_active if employee else True,
        }

        submit_text = "Сохранить изменения" if employee else "Добавить нового сотрудника"

        return {
            "title": title,
            "schema": schema,
            "values": values,
            "submitText": submit_text,
        }

    @classmethod
    def save(cls, doctorprofile: DoctorProfile, form_data: Dict[str, Any]):
        hospital_id = cls.get_current_hospital_id(doctorprofile)
        employee_id = form_data.get('id')
        form_values = form_data.get('values', {})
        family = form_values.get('family')
        name = form_values.get('name')
        patronymic = form_values.get('patronymic')
        is_active = form_values.get('isActive', True)

        try:
            if employee_id is None:
                employee = Employee.add(hospital_id, family, name, patronymic, doctorprofile, as_object=True)
            else:
                employee = Employee.edit(hospital_id, employee_id, family, name, patronymic, is_active, doctorprofile, as_object=True)
        except ValueError as e:
            return {
                "ok": False,
                "message": str(e),
                "result": {},
            }
        else:
            employee_json = cls._json(employee)
            return {
                "ok": True,
                "message": f"Сотрудник \"{employee_json['fullName']}\" успешно сохранён",
                "result": employee_json,
            }
