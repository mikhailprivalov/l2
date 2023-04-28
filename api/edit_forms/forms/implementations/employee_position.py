from typing import Any, Dict, Optional
from api.edit_forms.forms.base import BaseForm, FormObjectNotFoundException, HospitalObjectView
from employees.models import Position
from laboratory.utils import strfdatetime
from users.models import DoctorProfile


class EmployeePositionForm(BaseForm, HospitalObjectView[Position]):
    access_groups_to_edit = ('Конструктор: Настройка организации',)
    model: Position = Position

    @staticmethod
    def _json(object: Position) -> Optional[Dict[str, Any]]:
        return {
            'id': object.id,
            'name': object.name,
            'hospitalId': object.hospital_id,
            'isActive': object.is_active,
            'createdAt': strfdatetime(object.created_at, "%d.%m.%Y %X"),
            'whoCreate': object.doctorprofile_created.get_fio() if object.doctorprofile_created else None,
            'updatedAt': strfdatetime(object.updated_at, "%d.%m.%Y %X") if object.updated_at else None,
            'whoUpdate': object.doctorprofile_updated.get_fio() if object.doctorprofile_updated else None,
        }

    @classmethod
    def get_form_data(cls, doctorprofile: DoctorProfile, form_data: Dict[str, Any]):
        hospital = cls.get_current_hospital(doctorprofile)
        position_id = form_data.get('id')
        position = None

        if position_id is not None:
            position = cls.get_by_id(doctorprofile, position_id)
            if not position:
                raise FormObjectNotFoundException(f'Position with id {position_id} not found')

        title = f"Редактирование должности {position.name}" if position else "Добавление новой должности"

        schema = [
            {"component": "h5", "children": f"Организация: {hospital.safe_short_title}"},
            {"label": "Название должности", "validation-name": "Название", "name": "name", "validation": "required:trim"},
        ]

        if position:
            schema.append(
                {
                    "label": "Должность активна",
                    "name": "isActive",
                    "type": "checkbox",
                }
            )

        values = {
            "name": position.name if position else "",
            "isActive": position.is_active if position else True,
        }

        submit_text = "Сохранить изменения" if position else "Добавить новую должность"

        return {
            "title": title,
            "schema": schema,
            "values": values,
            "submitText": submit_text,
        }

    @classmethod
    def save(cls, doctorprofile: DoctorProfile, form_data: Dict[str, Any]):
        hospital_id = cls.get_current_hospital_id(doctorprofile)
        position_id = form_data.get('id')
        form_values = form_data.get('values', {})
        name = form_values.get('name')
        is_active = form_values.get('isActive', True)

        try:
            if position_id is None:
                position = Position.add(hospital_id, name, doctorprofile)
            else:
                position = Position.edit(hospital_id, position_id, name, is_active, doctorprofile)
        except ValueError as e:
            return {
                "ok": False,
                "message": str(e),
                "result": {},
            }
        else:
            return {
                "ok": True,
                "message": f"Должность \"{position['name']}\" успешно сохранена",
                "result": position,
            }
