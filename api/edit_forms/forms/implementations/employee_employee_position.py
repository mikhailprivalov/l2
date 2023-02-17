from typing import Any, Dict, Optional
from api.edit_forms.forms.base import BaseForm, FormObjectNotFoundException, HospitalObjectView
from api.edit_forms.forms.implementations.employee_employee import EmployeeEmployeeForm
from api.edit_forms.forms.implementations.employee_position import EmployeePositionForm
from employees.models import EmployeePosition
from laboratory.utils import strfdatetime
from users.models import DoctorProfile


class EmployeeEmployeePositionForm(BaseForm, HospitalObjectView[EmployeePosition]):
    access_groups_to_edit = ('Конструктор: Настройка организации',)
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
            'employeeName': employee_json['fullName'],
            'positionName': position_json['name'],
            'departmentId': object.department_id,
            'rate': object.rate,
            'isActive': object.is_active,
            'isActiveText': 'да' if object.is_active else 'нет',
            'createdAt': strfdatetime(object.created_at, "%d.%m.%Y %X"),
            'whoCreate': object.doctorprofile_created.get_fio() if object.doctorprofile_created else None,
            'updatedAt': strfdatetime(object.updated_at, "%d.%m.%Y %X") if object.updated_at else None,
            'whoUpdate': object.doctorprofile_updated.get_fio() if object.doctorprofile_updated else None,
        }

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
        ]
