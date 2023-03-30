from enum import Enum

from django.db.models import Q
from typing import Any, Dict, Generic, Optional, Tuple, TypeVar

from django.db import models
from django.core.paginator import Paginator
from hospitals.models import Hospitals

from users.models import DoctorProfile
from utils.classes import Static


class FormException(Exception):
    pass


class FormNotFoundException(FormException):
    pass


class FormForbiddenException(FormException):
    pass


class FormObjectNotFoundException(FormException):
    pass


ANY_GROUP = '*'
ANY_GROUPS = (ANY_GROUP,)


def has_access(doctorprofile: DoctorProfile, groups: Tuple):
    if not groups:
        raise Exception('Access groups not configured')
    if not doctorprofile.user.is_staff and not set(ANY_GROUPS).intersection(set(groups)) and not doctorprofile.is_member(groups):
        raise FormForbiddenException(f'Access is prohibited: access={groups}, user={[str(x) for x in doctorprofile.user.groups.all()]}')


class BaseForm(Static):
    access_groups_to_edit: Tuple = tuple()

    @classmethod
    def get_markup(cls, doctorprofile: DoctorProfile, form_data: Dict[str, Any]):
        has_access(doctorprofile, cls.access_groups_to_edit)
        return cls.get_form_data(doctorprofile, form_data)

    @classmethod
    def get_form_data(cls, doctorprofile: DoctorProfile, form_data: Dict[str, Any]):
        return {
            "title": "",
            # documentation https://vueformulate.com/guide/forms/generating-forms/#schemas
            "schema": [{}],
            "values": {},
            "submitText": "",
        }

    @classmethod
    def save(cls, doctorprofile: DoctorProfile, form_data: Dict[str, Any]):
        return {
            "ok": True,
            "message": "BaseForm объект сохранён",
            "result": {},
        }


ObjectType = TypeVar('ObjectType', bound=models.Model)


class SortDirections(Enum):
    ASC = 'asc'
    DESC = 'desc'


class ObjectView(Static, Generic[ObjectType]):
    access_groups_to_view: Tuple = ANY_GROUPS
    model: ObjectType

    @classmethod
    def _get_by_id(cls, doctorprofile: DoctorProfile, object_id: int) -> Optional[ObjectType]:
        return cls.model.objects.filter(id=object_id).first()

    @classmethod
    def get_by_id(cls, doctorprofile: DoctorProfile, object_id: int) -> Optional[ObjectType]:
        has_access(doctorprofile, cls.access_groups_to_view)
        return cls._get_by_id(doctorprofile, object_id)

    @staticmethod
    def list_name():
        return 'name'

    # Массив колонок https://happy-coding-clans.github.io/vue-easytable/#/en/doc/table/api?anchor=column-option
    # field - поле из _json
    @staticmethod
    def _table_columns():
        return [
            {
                'field': 'id',
                'key': 'id',
                'title': 'Идентификатор',
                'align': "left",
            },
            {
                'field': 'name',
                'key': 'name',
                'title': 'Название',
                'align': "left",
            },
        ]

    @classmethod
    def table_columns(cls):
        return cls._table_columns()

    @classmethod
    def view_params(cls):
        return {
            "listName": cls.list_name(),
            "tableColumns": cls.table_columns(),
        }

    @staticmethod
    def _json(object: ObjectType) -> Optional[Dict[str, Any]]:
        return {
            "id": object.pk,
            "name": object.name,
        }

    @classmethod
    def _treeselect(cls, json_object: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not json_object:
            return None
        return {
            "id": json_object.get('id'),
            "label": json_object.get(cls.list_name()),
        }

    @staticmethod
    def _search_filters(search: str):
        return [
            {
                "name__istartswith": search,
            }
        ]

    @classmethod
    def json(cls, doctorprofile: DoctorProfile, object: ObjectType) -> Optional[Dict[str, Any]]:
        has_access(doctorprofile, cls.access_groups_to_view)
        return cls._json(object)

    @classmethod
    def json_by_id(cls, doctorprofile: DoctorProfile, object_id: int) -> Optional[Dict[str, Any]]:
        has_access(doctorprofile, cls.access_groups_to_view)
        object = cls._get_by_id(doctorprofile, object_id)

        if not object:
            return None

        return cls._json(object)

    @classmethod
    def _default_rows(cls, doctorprofile: DoctorProfile):
        return cls.model.objects.all()

    @classmethod
    def _default_filter(cls, doctorprofile: DoctorProfile) -> Dict[str, Any]:
        return {}

    @classmethod
    def search(
        cls,
        doctorprofile: DoctorProfile,
        page: int = 1,
        per_page: int = 30,
        sort_column: Optional[str] = None,
        sort_direction: Optional[SortDirections] = None,
        filter: Optional[Dict[str, Any]] = None,
        return_total_rows: bool = False,
        as_treeselect: bool = False,
        search: Optional[str] = None,
    ):
        has_access(doctorprofile, cls.access_groups_to_view)
        objects = cls._default_rows(doctorprofile)

        filters = {
            **cls._default_filter(doctorprofile),
            **(filter or {}),
        }

        if filters:
            objects = objects.filter(**filters)

        if search:
            q_objects = Q()
            search_tokens = cls._search_filters(search)
            for t in search_tokens:
                q_objects |= Q(**t)
            objects = objects.filter(q_objects)

        if sort_column:
            objects = objects.order_by(f'{"-" if sort_direction == SortDirections.DESC else ""}{sort_column}')

        rows = objects
        total_pages = 1
        if not return_total_rows:
            paginator = Paginator(objects, per_page)
            rows = paginator.get_page(page)
            total_pages = paginator.num_pages

        rows = [cls._json(o) for o in rows]

        if as_treeselect:
            rows = [cls._treeselect(o) for o in rows]

        return {
            "page": page,
            "perPage": per_page,
            "pages": total_pages,
            "totalCount": objects.count(),
            "rows": rows,
        }


class HospitalObjectView(ObjectView[ObjectType]):
    @staticmethod
    def get_current_hospital(doctorprofile: DoctorProfile) -> Hospitals:
        return doctorprofile.get_hospital()

    @staticmethod
    def get_current_hospital_id(doctorprofile: DoctorProfile) -> Hospitals:
        return doctorprofile.get_hospital_id()

    @staticmethod
    def _get_object_hospital_id(object) -> int:
        return object.hospital_id

    @classmethod
    def _get_by_id(cls, doctorprofile: DoctorProfile, object_id: int) -> Optional[ObjectType]:
        object = super()._get_by_id(doctorprofile, object_id)
        if not object:
            return None

        hospital_id = cls.get_current_hospital_id(doctorprofile)

        if cls._get_object_hospital_id(object) != hospital_id:
            return None

        return object

    @staticmethod
    def _map_hospital_id_to_query(hospital_id: int) -> Dict[str, Any]:
        return dict(hospital_id=hospital_id)

    @classmethod
    def _default_filter(cls, doctorprofile: DoctorProfile) -> Dict[str, Any]:
        hospital_id = cls.get_current_hospital_id(doctorprofile)
        return cls._map_hospital_id_to_query(hospital_id)
