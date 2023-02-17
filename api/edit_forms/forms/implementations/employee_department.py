from typing import Any, Dict, Optional
from api.edit_forms.forms.base import BaseForm, FormObjectNotFoundException, HospitalObjectView
from employees.models import Department, EmployeePosition
from laboratory.utils import strfdatetime
from users.models import DoctorProfile


class EmployeeDepartmentForm(BaseForm, HospitalObjectView[Department]):
    access_groups_to_edit = ('Конструктор: Настройка организации',)
    model: Department = Department

    @staticmethod
    def _json(object: Department) -> Optional[Dict[str, Any]]:
        return {
            'id': object.id,
            'name': object.name,
            'hospitalId': object.hospital_id,
            'isActive': object.is_active,
            'childrenElementsCount': EmployeePosition.objects.filter(department=object, is_active=True).count(),
            'createdAt': strfdatetime(object.created_at, "%d.%m.%Y %X"),
            'whoCreate': object.doctorprofile_created.get_fio() if object.doctorprofile_created else None,
            'updatedAt': strfdatetime(object.updated_at, "%d.%m.%Y %X") if object.updated_at else None,
            'whoUpdate': object.doctorprofile_updated.get_fio() if object.doctorprofile_updated else None,
        }

    @classmethod
    def get_form_data(cls, doctorprofile: DoctorProfile, form_data: Dict[str, Any]):
        hospital = cls.get_current_hospital(doctorprofile)
        department_id = form_data.get('id')
        department = None

        if department_id is not None:
            department = cls.get_by_id(doctorprofile, department_id)
            if not department:
                raise FormObjectNotFoundException(f'Department with id {department_id} not found')

        title = f"Редактирование отдела {department.name}" if department else "Добавление нового отдела"

        schema = [
            {"component": "h5", "children": f"Организация: {hospital.safe_short_title}"},
            {"label": "Название отдела", "validation-name": "Название", "name": "name", "validation": "required:trim"},
        ]

        if department:
            schema.append(
                {
                    "label": "Отдел активен",
                    "name": "isActive",
                    "type": "checkbox",
                }
            )

        values = {
            "name": department.name if department else "",
            "isActive": department.is_active if department else True,
        }

        submit_text = "Сохранить изменения" if department else "Добавить новый отдел"

        return {
            "title": title,
            "schema": schema,
            "values": values,
            "submitText": submit_text,
        }

    @classmethod
    def save(cls, doctorprofile: DoctorProfile, form_data: Dict[str, Any]):
        hospital_id = cls.get_current_hospital_id(doctorprofile)
        department_id = form_data.get('id')
        form_values = form_data.get('values', {})
        name = form_values.get('name')
        is_active = form_values.get('isActive', True)

        try:
            if department_id is None:
                department = Department.add(hospital_id, name, doctorprofile)
            else:
                department = Department.edit(hospital_id, department_id, name, is_active, doctorprofile)
        except ValueError as e:
            return {
                "ok": False,
                "message": str(e),
                "result": {},
            }
        else:
            return {
                "ok": True,
                "message": f"Отделение \"{department['name']}\" успешно сохранено",
                "result": department,
            }
