import os
import uuid

import simplejson as json
from django.contrib.postgres.fields import ArrayField
from django.db import IntegrityError, models, transaction

from hospitals.models import Hospitals
from podrazdeleniya.models import Podrazdeleniya
from users.models import DoctorProfile

LAYOUT_TEMPLATE_FIELD_TYPE = 41
ADDRESSEE_FIELD_TYPE = 45
MENTEE_FIELD_TYPE = 46
MENTOR_FIELD_TYPE = 47


def layout_template_is_simple(research):
    from directory.models import ParaclinicInputField

    if not research:
        return False
    return not ParaclinicInputField.objects.filter(group__research=research, field_type=LAYOUT_TEMPLATE_FIELD_TYPE).exists()


class GroupDocuments(models.Model):
    title = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        verbose_name = "Группа Документов"
        verbose_name_plural = "Группы документов"

    def __str__(self):
        return f"{self.title}"

    @property
    def json(self):
        return {
            "id": self.id,
            "title": self.title or "",
        }

    @staticmethod
    def get_list():
        return [row.json for row in GroupDocuments.objects.all().order_by("title", "pk")]

    @staticmethod
    def save_group(pk, title):
        title = (title or "").strip()
        if not title:
            return {"ok": False, "message": "Укажите название"}
        if pk in (None, -1, "-1"):
            obj = GroupDocuments(title=title)
        else:
            obj = GroupDocuments.objects.filter(pk=pk).first()
            if not obj:
                return {"ok": False, "message": "Группа не найдена"}
            obj.title = title
        obj.save()
        return {"ok": True, "id": obj.pk, "title": obj.title}


class AddresseeGroup(models.Model):
    ALL_ID = 0
    ALL_TITLE = "Все"
    ALL_GROUP = "Все адресаты"
    CONSTRUCTOR_GROUP = "Конструктор: ДОУ"

    title = models.CharField(max_length=128, blank=True, null=True)
    hide = models.BooleanField(default=False, blank=True, db_index=True)
    order = models.IntegerField(default=0)
    who_create = models.ForeignKey(
        DoctorProfile,
        related_name="addressee_groups",
        db_index=True,
        default=None,
        blank=True,
        null=True,
        help_text="Автор личного набора; пусто — общий набор конструктора",
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = "Набор адресатов"
        verbose_name_plural = "Наборы адресатов"
        ordering = ("order", "title", "pk")

    def __str__(self):
        return self.title or ""

    @property
    def json(self):
        return {
            "id": self.id,
            "title": self.title or "",
            "hide": self.hide,
            "order": self.order,
            "own": False,
        }

    def as_json(self, doctor_id=None):
        data = self.json
        data["own"] = bool(self.who_create_id and doctor_id and self.who_create_id == doctor_id)
        return data

    @staticmethod
    def _employee_json(doctor):
        return {
            "id": doctor.pk,
            "fio": doctor.get_fio(),
            "department": doctor.podrazdeleniye.title if doctor.podrazdeleniye else "",
        }

    @classmethod
    def can_see_all(cls, user):
        if not user:
            return False
        if getattr(user, "is_superuser", False):
            return True
        return user.groups.filter(name=cls.ALL_GROUP).exists()

    @classmethod
    def can_list_all_employees(cls, user, doctor=None):
        if cls.can_see_all(user):
            return True
        if doctor and doctor.has_group(cls.CONSTRUCTOR_GROUP):
            return True
        return bool(user and user.groups.filter(name=cls.CONSTRUCTOR_GROUP).exists())

    @classmethod
    def empty_employees(cls, page=1, page_size=100):
        return {
            "result": [],
            "total": 0,
            "page": page,
            "pageSize": page_size if page_size is not None else 0,
            "hasMore": False,
        }

    @classmethod
    def get_list(cls, include_all=True, include_hidden=False, doctor_id=None, global_only=False):
        rows = cls.objects.all().order_by("order", "title", "pk")
        if global_only or not doctor_id:
            rows = rows.filter(who_create__isnull=True)
        else:
            rows = rows.filter(models.Q(who_create__isnull=True) | models.Q(who_create_id=doctor_id))
        if not include_hidden:
            rows = rows.filter(hide=False)
        result = []
        if include_all:
            result.append({"id": cls.ALL_ID, "title": cls.ALL_TITLE, "hide": False, "order": -1, "own": False})
        result.extend([row.as_json(doctor_id) for row in rows])
        return result

    @classmethod
    def get_details(cls, pk):
        if pk in (None, cls.ALL_ID, 0, "0", -1, "-1"):
            return {"ok": False, "message": "Набор не найден"}
        obj = cls.objects.filter(pk=pk).first()
        if not obj:
            return {"ok": False, "message": "Набор не найден"}
        members = [cls._employee_json(row.doctor) for row in obj.members.select_related("doctor__podrazdeleniye").order_by("doctor__family", "doctor__name", "pk") if row.doctor_id]
        payload = obj.json
        payload["ok"] = True
        payload["members"] = members
        return payload

    @classmethod
    def _set_members(cls, obj, member_ids):
        ids = []
        seen = set()
        for raw in member_ids:
            try:
                doctor_id = int(raw)
            except (TypeError, ValueError):
                continue
            if doctor_id < 1 or doctor_id in seen:
                continue
            seen.add(doctor_id)
            ids.append(doctor_id)
        valid = set(DoctorProfile.objects.filter(pk__in=ids).values_list("pk", flat=True))
        ids = [doctor_id for doctor_id in ids if doctor_id in valid]
        obj.members.all().delete()
        AddresseeGroupMember.objects.bulk_create([AddresseeGroupMember(group=obj, doctor_id=doctor_id) for doctor_id in ids])
        return ids

    @classmethod
    def save_group(cls, pk, title, hide=False, member_ids=None):
        title = (title or "").strip()
        if not title:
            return {"ok": False, "message": "Укажите название"}
        if pk in (None, -1, "-1"):
            obj = cls(title=title, hide=bool(hide))
        else:
            obj = cls.objects.filter(pk=pk, who_create__isnull=True).first()
            if not obj:
                return {"ok": False, "message": "Набор не найден"}
            obj.title = title
            obj.hide = bool(hide)
        obj.save()
        if member_ids is not None:
            cls._set_members(obj, member_ids)
        return {"ok": True, "id": obj.pk, "title": obj.title}

    @classmethod
    def save_personal(cls, who_create, title, member_ids):
        if not who_create:
            return {"ok": False, "message": "Нет пользователя"}
        title = (title or "").strip()
        if not title:
            return {"ok": False, "message": "Укажите название"}
        if not member_ids:
            return {"ok": False, "message": "Выберите сотрудников"}
        obj = cls(title=title, who_create=who_create)
        obj.save()
        cls._set_members(obj, member_ids)
        return {"ok": True, "id": obj.pk, "title": obj.title, "own": True}

    @classmethod
    def delete_personal(cls, pk, who_create):
        if not who_create:
            return {"ok": False, "message": "Нет пользователя"}
        obj = cls.objects.filter(pk=pk, who_create=who_create).first()
        if not obj:
            return {"ok": False, "message": "Набор не найден"}
        obj.delete()
        return {"ok": True}

    @classmethod
    def get_employees(cls, group_id, hospital_id, query="", page=1, page_size=100, allow_all=False):
        try:
            group_id = int(group_id)
        except (TypeError, ValueError):
            group_id = cls.ALL_ID
        if (not group_id or group_id <= 0) and not allow_all:
            return cls.empty_employees(page, page_size)
        doctors = DoctorProfile.objects.filter(user__is_active=True, is_system_user=False).select_related("user", "podrazdeleniye")
        if group_id and group_id > 0:
            doctors = doctors.filter(addressee_group_members__group_id=group_id)
        query = (query or "").strip()
        if query:
            parts = [p for p in query.split() if p]
            q_filter = models.Q()
            for part in parts:
                q_filter &= models.Q(family__icontains=part) | models.Q(name__icontains=part) | models.Q(patronymic__icontains=part) | models.Q(fio__icontains=part)
            doctors = doctors.filter(q_filter)
        doctors = doctors.distinct().order_by("family", "name", "patronymic", "pk")
        total = doctors.count()
        if page_size is None:
            page = 1
            rows = doctors
            has_more = False
        else:
            try:
                page = max(int(page or 1), 1)
            except (TypeError, ValueError):
                page = 1
            try:
                page_size = max(int(page_size or 100), 1)
            except (TypeError, ValueError):
                page_size = 100
            start = (page - 1) * page_size
            rows = doctors[start : start + page_size]
            has_more = start + page_size < total
        return {
            "result": [cls._employee_json(row) for row in rows],
            "total": total,
            "page": page,
            "pageSize": page_size if page_size is not None else total,
            "hasMore": has_more,
        }


class AddresseeGroupMember(models.Model):
    group = models.ForeignKey(AddresseeGroup, related_name="members", on_delete=models.CASCADE)
    doctor = models.ForeignKey(DoctorProfile, related_name="addressee_group_members", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Сотрудник набора адресатов"
        verbose_name_plural = "Сотрудники наборов адресатов"
        unique_together = ("group", "doctor")

    def __str__(self):
        return f"{self.group} {self.doctor}"


class TypeDocuments(models.Model):
    title = models.CharField(max_length=128, blank=True, null=True)
    group_document = models.ForeignKey(GroupDocuments, default=None, blank=True, null=True, help_text="Группа документов", on_delete=models.SET_NULL)
    code = models.CharField(max_length=55, blank=True, null=True)
    layout_template = models.ForeignKey(
        "directory.Researches",
        default=None,
        blank=True,
        null=True,
        db_index=True,
        help_text="Шаблон документа",
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = "Вид документа"
        verbose_name_plural = "Виды документов"

    def __str__(self):
        return f"{self.title}"

    def get_layout_templates(self):
        prefetched = getattr(self, "_prefetched_objects_cache", {}).get("layout_template_links")
        if prefetched is not None:
            templates = [row.layout_template for row in prefetched if row.layout_template_id]
        else:
            templates = [row.layout_template for row in self.layout_template_links.select_related("layout_template").order_by("order", "pk") if row.layout_template_id]
        if templates:
            return templates
        if self.layout_template_id and self.layout_template:
            return [self.layout_template]
        return []

    def get_creators(self):
        prefetched = getattr(self, "_prefetched_objects_cache", {}).get("creators")
        if prefetched is not None:
            rows = prefetched
        else:
            rows = self.creators.select_related("doctor__podrazdeleniye").order_by("doctor__family", "doctor__name", "pk")
        return [AddresseeGroup._employee_json(row.doctor) for row in rows if row.doctor_id]

    def can_create(self, doctor):
        if not doctor:
            return False
        creator_ids = list(self.creators.values_list("doctor_id", flat=True))
        if not creator_ids:
            return True
        return doctor.pk in creator_ids

    @property
    def json(self):
        templates = self.get_layout_templates()
        template_ids = [row.pk for row in templates]
        return {
            "id": self.id,
            "title": self.title or "",
            "code": self.code or "",
            "groupId": self.group_document_id,
            "groupTitle": self.group_document.title if self.group_document else "",
            "layoutTemplateId": template_ids[0] if template_ids else self.layout_template_id,
            "layoutTemplateIds": template_ids,
            "layoutTemplates": [{"id": row.pk, "label": row.title} for row in templates],
            "creators": self.get_creators(),
        }

    @staticmethod
    def get_list(group_id=None, doctor=None, available_only=False):
        qs = (
            TypeDocuments.objects.select_related("group_document", "layout_template")
            .prefetch_related(
                models.Prefetch(
                    "layout_template_links",
                    queryset=TypeDocumentLayoutTemplate.objects.select_related("layout_template").order_by("order", "pk"),
                ),
                models.Prefetch(
                    "creators",
                    queryset=TypeDocumentCreator.objects.select_related("doctor__podrazdeleniye").order_by("doctor__family", "doctor__name", "pk"),
                ),
            )
            .order_by("title", "pk")
        )
        if group_id in (-1, "-1"):
            qs = qs.filter(group_document__isnull=True)
        elif group_id not in (None, "", 0, "0"):
            qs = qs.filter(group_document_id=group_id)
        if available_only:
            if not doctor:
                return []
            has_creators = TypeDocumentCreator.objects.filter(type_document_id=models.OuterRef("pk"))
            is_creator = TypeDocumentCreator.objects.filter(type_document_id=models.OuterRef("pk"), doctor=doctor)
            qs = qs.filter(~models.Exists(has_creators) | models.Exists(is_creator))
        return [row.json for row in qs]

    @staticmethod
    def _parse_template_ids(layout_template_ids, layout_template_id):
        raw = layout_template_ids
        if raw is None:
            raw = [layout_template_id] if layout_template_id not in (None, "", -1, "-1") else []
        if not isinstance(raw, (list, tuple)):
            raw = [raw]
        seen = set()
        result = []
        for item in raw:
            if item in (None, "", -1, "-1"):
                continue
            try:
                value = int(item)
            except (TypeError, ValueError):
                continue
            if value <= 0 or value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result

    @staticmethod
    def _parse_creator_ids(creator_ids):
        if not isinstance(creator_ids, (list, tuple)):
            creator_ids = [] if creator_ids in (None, "", -1, "-1") else [creator_ids]
        seen = set()
        result = []
        for item in creator_ids:
            if isinstance(item, dict):
                item = item.get("id")
            if item in (None, "", -1, "-1"):
                continue
            try:
                value = int(item)
            except (TypeError, ValueError):
                continue
            if value <= 0 or value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result

    @staticmethod
    def _set_creators(obj, creator_ids):
        ids = TypeDocuments._parse_creator_ids(creator_ids)
        valid = set(DoctorProfile.objects.filter(pk__in=ids).values_list("pk", flat=True))
        ids = [doctor_id for doctor_id in ids if doctor_id in valid]
        TypeDocumentCreator.objects.filter(type_document=obj).delete()
        TypeDocumentCreator.objects.bulk_create([TypeDocumentCreator(type_document=obj, doctor_id=doctor_id) for doctor_id in ids])
        return ids

    @staticmethod
    def save_type(pk, title, group_id=None, code="", layout_template_id=None, layout_template_ids=None, creator_ids=None):
        from directory.models import Researches

        title = (title or "").strip()
        if not title:
            return {"ok": False, "message": "Укажите название"}
        group = None
        if group_id not in (None, "", -1, "-1"):
            group = GroupDocuments.objects.filter(pk=group_id).first()
            if not group:
                return {"ok": False, "message": "Группа не найдена"}
        template_ids = TypeDocuments._parse_template_ids(layout_template_ids, layout_template_id)
        templates = []
        for template_id in template_ids:
            layout_template = Researches.objects.filter(pk=template_id, is_layout_template=True).first()
            if not layout_template:
                return {"ok": False, "message": "Шаблон не найден"}
            if not layout_template_is_simple(layout_template):
                return {"ok": False, "message": f"Шаблон «{layout_template.title}» содержит вложенный шаблон"}
            templates.append(layout_template)
        first_template = templates[0] if templates else None
        with transaction.atomic():
            if pk in (None, -1, "-1"):
                obj = TypeDocuments(title=title, group_document=group, code=code or "", layout_template=first_template)
            else:
                obj = TypeDocuments.objects.filter(pk=pk).first()
                if not obj:
                    return {"ok": False, "message": "Вид документа не найден"}
                obj.title = title
                obj.group_document = group
                obj.code = code or ""
                obj.layout_template = first_template
            obj.save()
            TypeDocumentLayoutTemplate.objects.filter(type_document=obj).delete()
            TypeDocumentLayoutTemplate.objects.bulk_create([TypeDocumentLayoutTemplate(type_document=obj, layout_template=row, order=index) for index, row in enumerate(templates)])
            if creator_ids is not None:
                TypeDocuments._set_creators(obj, creator_ids)
            if templates:
                TypeDocumentsSchema.get_or_create_for_type(obj)
        return {"ok": True, "id": obj.pk, "title": obj.title}


class TypeDocumentLayoutTemplate(models.Model):
    type_document = models.ForeignKey(TypeDocuments, related_name="layout_template_links", on_delete=models.CASCADE)
    layout_template = models.ForeignKey("directory.Researches", related_name="type_document_links", on_delete=models.CASCADE)
    order = models.IntegerField(default=0, db_index=True)

    class Meta:
        verbose_name = "Шаблон вида документа"
        verbose_name_plural = "Шаблоны видов документов"
        ordering = ["order", "pk"]
        unique_together = ("type_document", "layout_template")

    def __str__(self):
        return f"{self.type_document} – {self.layout_template} ({self.order})"


class TypeDocumentCreator(models.Model):
    type_document = models.ForeignKey(TypeDocuments, related_name="creators", on_delete=models.CASCADE)
    doctor = models.ForeignKey(DoctorProfile, related_name="type_document_creators", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Создатель вида документа"
        verbose_name_plural = "Создатели видов документов"
        unique_together = ("type_document", "doctor")

    def __str__(self):
        return f"{self.type_document} {self.doctor}"


class TypeCases(models.Model):
    title = models.CharField(max_length=128, blank=True, null=True)
    code = models.CharField(max_length=55, blank=True, null=True)
    default_type_document = models.ForeignKey(
        TypeDocuments,
        default=None,
        blank=True,
        null=True,
        db_index=True,
        help_text="Документ по умолчанию при создании дела",
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = "Вид дела"
        verbose_name_plural = "Виды дел"

    def __str__(self):
        return f"{self.title}"

    @property
    def json(self):
        type_doc = self.default_type_document
        return {
            "id": self.id,
            "title": self.title or "",
            "code": self.code or "",
            "defaultTypeDocumentId": self.default_type_document_id,
            "defaultTypeDocumentTitle": type_doc.title if type_doc else "",
        }

    @staticmethod
    def get_list():
        qs = TypeCases.objects.select_related("default_type_document").order_by("title", "pk")
        return [row.json for row in qs]

    @staticmethod
    def save_case(pk, title, code="", default_type_document_id=None):
        title = (title or "").strip()
        if not title:
            return {"ok": False, "message": "Укажите название"}
        if default_type_document_id in (None, "", -1, "-1"):
            return {"ok": False, "message": "Укажите документ по умолчанию"}
        type_doc = TypeDocuments.objects.filter(pk=default_type_document_id).first()
        if not type_doc:
            return {"ok": False, "message": "Вид документа не найден"}
        if pk in (None, -1, "-1"):
            obj = TypeCases(title=title, code=code or "", default_type_document=type_doc)
        else:
            obj = TypeCases.objects.filter(pk=pk).first()
            if not obj:
                return {"ok": False, "message": "Вид дела не найден"}
            obj.title = title
            obj.code = code or ""
            obj.default_type_document = type_doc
        obj.save()
        return {"ok": True, "id": obj.pk, "title": obj.title}


class DocumentFieldGroups(models.Model):
    title = models.CharField(max_length=550, help_text="Название группы")
    show_title = models.BooleanField(default=True, blank=True)
    type_document = models.ForeignKey(TypeDocuments, db_index=True, on_delete=models.CASCADE, help_text="Вид документа")
    order = models.IntegerField()
    hide = models.BooleanField(default=False, blank=True)
    visibility = models.TextField(default="", blank=True)
    fields_inline = models.BooleanField(default=False, blank=True)

    class Meta:
        verbose_name = "Группа полей документа"
        verbose_name_plural = "Группы полей документа"

    def __str__(self):
        return f"{self.type_document} – {self.title}"

    def as_json(self):
        return {
            "pk": self.pk,
            "order": self.order,
            "title": self.title,
            "show_title": self.show_title,
            "hide": self.hide,
            "visibility": self.visibility,
            "fieldsInline": self.fields_inline,
            "fields": [field.as_json() for field in self.fields.all().order_by("order")],
        }

    @staticmethod
    def get_structure(type_document_id):
        type_doc = TypeDocuments.objects.filter(pk=type_document_id).first()
        if not type_doc:
            return {"ok": False, "message": "Вид документа не найден"}
        groups = [group.as_json() for group in DocumentFieldGroups.objects.filter(type_document=type_doc).prefetch_related("fields").order_by("order")]
        orphan_fields = DocumentFields.objects.filter(type_document=type_doc, group__isnull=True).order_by("order")
        if orphan_fields.exists():
            next_order = max([group["order"] for group in groups], default=0) + 1
            groups.append(
                {
                    "pk": -1,
                    "order": next_order,
                    "title": "Основное",
                    "show_title": True,
                    "hide": False,
                    "visibility": "",
                    "fieldsInline": False,
                    "fields": [field.as_json() for field in orphan_fields],
                }
            )
        return {"ok": True, "id": type_doc.pk, "title": type_doc.title or "", "code": type_doc.code or "", "groups": groups}

    @staticmethod
    @transaction.atomic
    def save_structure(type_document_id, groups):
        type_doc = TypeDocuments.objects.filter(pk=type_document_id).first()
        if not type_doc:
            return {"ok": False, "message": "Вид документа не найден"}
        for group_data in groups or []:
            group_pk = group_data.get("pk", -1)
            if group_pk in (None, -1, "-1"):
                group = DocumentFieldGroups(
                    title=group_data.get("title") or "",
                    show_title=bool(group_data.get("show_title", True)),
                    type_document=type_doc,
                    order=int(group_data.get("order") or 0),
                    hide=bool(group_data.get("hide", False)),
                    visibility=group_data.get("visibility") or "",
                    fields_inline=bool(group_data.get("fieldsInline", False)),
                )
            else:
                group = DocumentFieldGroups.objects.filter(pk=group_pk, type_document=type_doc).first()
                if not group:
                    continue
                group.title = group_data.get("title") or ""
                group.show_title = bool(group_data.get("show_title", True))
                group.order = int(group_data.get("order") or 0)
                group.hide = bool(group_data.get("hide", False))
                group.visibility = group_data.get("visibility") or ""
                group.fields_inline = bool(group_data.get("fieldsInline", False))
            group.save()
            for field_data in group_data.get("fields") or []:
                DocumentFields.save_field(type_doc, group, field_data)
        return {"ok": True, "id": type_doc.pk}


class Nomenclature(models.Model):
    title = models.CharField(max_length=128, blank=True, null=True)
    type_document = models.ForeignKey(TypeDocuments, default=None, blank=True, null=True, db_index=True, help_text="Тип документа", on_delete=models.SET_NULL)
    department = models.ForeignKey(
        Podrazdeleniya, related_name="department_nomenclature", help_text="Подразделение", db_index=True, null=True, blank=True, default=None, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Номенклатура"
        verbose_name_plural = "Носенклатуры"

    def __str__(self):
        return f"{self.title}"


class Generators(models.Model):
    title = models.CharField(max_length=400, help_text="Название генератора номера")
    hospital = models.ForeignKey(Hospitals, on_delete=models.CASCADE, db_index=True, verbose_name="Больница")
    year = models.IntegerField(verbose_name="Год", db_index=True)
    is_active = models.BooleanField(verbose_name="Активность диапазона", db_index=True)
    start = models.PositiveBigIntegerField(verbose_name="Начало диапазона")
    end = models.PositiveBigIntegerField(verbose_name="Конец диапазона", null=True, blank=True, default=None)
    last = models.PositiveBigIntegerField(verbose_name="Последнее значение диапазона", null=True, blank=True)
    free_numbers = ArrayField(models.PositiveBigIntegerField(verbose_name="Свободные номера"), default=list, blank=True)
    prepend_length = models.PositiveSmallIntegerField(verbose_name="Длина номера", help_text='Если номер короче, впереди будет добавлено недостающее кол-во "0"')
    department = models.ForeignKey(
        Podrazdeleniya, related_name="department_for_generator", help_text="Подразделение", db_index=True, null=True, blank=True, default=None, on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"{self.hospital} {self.year} {self.is_active} {self.start} — {self.end} ({self.last})"

    class Meta:
        verbose_name = "Генератор номеров"
        verbose_name_plural = "Генераторы номеров"


class MetaFieldsForAllTypeDocuments(models.Model):
    TYPES = (
        (0, "Text"),
        (1, "Date"),
        (2, "Calc"),
        (3, "List"),
        (4, "Dict"),
        (5, "Radio"),
        (6, "Number"),
        (7, "Number range"),
        (8, "Time HH:MM"),
        (9, "Table"),
        (10, "Исполнитель"),
    )
    title = models.CharField(max_length=400, help_text="Название поля ввода")
    short_title = models.CharField(max_length=400, default="", blank=True, help_text="Синоним-короткое название поля ввода")
    order = models.IntegerField()
    default_value = models.TextField(blank=True, default="")
    input_templates = models.TextField()
    hide = models.BooleanField()
    lines = models.IntegerField(default=3)
    field_type = models.SmallIntegerField(default=0, choices=TYPES, blank=True)
    required = models.BooleanField(default=False, blank=True)

    class Meta:
        verbose_name = "Мета реквизит для всех документов"
        verbose_name_plural = "Мета реквизиты для всех документов"

    def __str__(self):
        return f"{self.title}"


class DocumentFields(models.Model):
    TYPES = (
        (0, "Text"),
        (1, "Date"),
        (2, "Calc"),
        (3, "List"),
        (4, "Dict"),
        (5, "Radio"),
        (6, "Number"),
        (7, "Number range"),
        (8, "Time HH:MM"),
        (9, "Table"),
        (10, "Исполнитель"),
    )
    type_document = models.ForeignKey(TypeDocuments, default=None, db_index=True, blank=True, null=True, help_text="Тип документа", on_delete=models.SET_NULL)
    group = models.ForeignKey("DocumentFieldGroups", related_name="fields", default=None, blank=True, null=True, db_index=True, help_text="Группа полей", on_delete=models.CASCADE)
    title = models.CharField(max_length=400, help_text="Название поля ввода")
    short_title = models.CharField(max_length=400, default="", blank=True, help_text="Синоним-короткое название поля ввода")
    order = models.IntegerField()
    default_value = models.TextField(blank=True, default="")
    input_templates = models.TextField()
    hide = models.BooleanField()
    lines = models.IntegerField(default=3)
    field_type = models.SmallIntegerField(default=0, choices=TYPES, blank=True)
    required = models.BooleanField(default=False, blank=True)
    is_meta_attributes = models.BooleanField(default=False, blank=True)
    is_content_attributes = models.BooleanField(default=False, blank=True)

    class Meta:
        verbose_name = "Реквизит для документа"
        verbose_name_plural = "Реквизит для документов"

    def __str__(self):
        return f"{self.type_document}"

    @staticmethod
    def _parse_templates(raw):
        if not raw:
            return []
        try:
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except (TypeError, ValueError):
            return []

    def as_json(self):
        return {
            "pk": self.pk,
            "order": self.order,
            "title": self.title,
            "short_title": self.short_title,
            "default": self.default_value,
            "values_to_input": self._parse_templates(self.input_templates),
            "new_value": "",
            "hide": self.hide,
            "lines": self.lines,
            "field_type": self.field_type,
            "required": self.required,
            "is_meta_attributes": self.is_meta_attributes,
            "is_content_attributes": self.is_content_attributes,
        }

    @staticmethod
    def save_field(type_doc, group, field_data):
        field_pk = field_data.get("pk", -1)
        values_to_input = field_data.get("values_to_input") or []
        if not isinstance(values_to_input, list):
            values_to_input = []
        templates = json.dumps(values_to_input)
        if field_pk in (None, -1, "-1"):
            field = DocumentFields(
                type_document=type_doc,
                group=group,
                title=field_data.get("title") or "",
                short_title=field_data.get("short_title") or "",
                order=int(field_data.get("order") or 0),
                default_value=field_data.get("default") or "",
                input_templates=templates,
                hide=bool(field_data.get("hide", False)),
                lines=int(field_data.get("lines") or 3),
                field_type=int(field_data.get("field_type") or 0),
                required=bool(field_data.get("required", False)),
                is_meta_attributes=bool(field_data.get("is_meta_attributes", False)),
                is_content_attributes=bool(field_data.get("is_content_attributes", False)),
            )
        else:
            field = DocumentFields.objects.filter(pk=field_pk).first()
            if not field:
                return
            field.type_document = type_doc
            field.group = group
            field.title = field_data.get("title") or ""
            field.short_title = field_data.get("short_title") or ""
            field.order = int(field_data.get("order") or 0)
            field.default_value = field_data.get("default") or ""
            field.input_templates = templates
            field.hide = bool(field_data.get("hide", False))
            field.lines = int(field_data.get("lines") or 3)
            field.field_type = int(field_data.get("field_type") or 0)
            field.required = bool(field_data.get("required", False))
            field.is_meta_attributes = bool(field_data.get("is_meta_attributes", False))
            field.is_content_attributes = bool(field_data.get("is_content_attributes", False))
        field.save()


class TypeDocumentsSchema(models.Model):
    type_document = models.ForeignKey(TypeDocuments, db_index=True, related_name="schemas", on_delete=models.CASCADE, help_text="Вид документа")
    version = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, help_text="Версия схемы")
    schema = models.JSONField(default=dict, blank=True, help_text="Снимок шаблона со всеми правилами")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, help_text="Дата создания версии")

    class Meta:
        verbose_name = "Схема вида документа"
        verbose_name_plural = "Схемы видов документов"
        ordering = ["-created_at"]

    def __str__(self):
        title = self.type_document.title if self.type_document else "Документ"
        return f"{title} {self.version}"

    @staticmethod
    def _schema_key(schema):
        return json.dumps(schema, sort_keys=True, ensure_ascii=False, default=str)

    @staticmethod
    def _parse_templates(raw):
        if not raw:
            return []
        try:
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except (TypeError, ValueError):
            return []

    @staticmethod
    def serialize_field(field):
        from directory.models import ParaclinicInputFieldFileSettings

        values_to_input = TypeDocumentsSchema._parse_templates(field.input_templates)
        field_type = field.field_type
        if field.required and field_type in [10, 12] and "- Не выбрано" not in values_to_input:
            values_to_input = ["- Не выбрано", *values_to_input]
        file_settings = None
        if field_type == 42:
            file_settings = ParaclinicInputFieldFileSettings.get_file_field_settings(field)
        return {
            "pk": field.pk,
            "order": field.order,
            "lines": field.lines,
            "title": field.title,
            "short_title": field.short_title or "",
            "hide": field.hide,
            "values_to_input": values_to_input,
            "field_type": field_type,
            "can_edit": field.can_edit_computed,
            "default_value": field.default_value or "",
            "visibility": field.visibility or "",
            "required": bool(field.required or field.required_set_by_admin),
            "required_set_by_admin": bool(field.required_set_by_admin),
            "helper": field.helper or "",
            "controlParam": field.control_param or "",
            "not_edit": field.not_edit,
            "operator_enter_param": field.operator_enter_param,
            "deniedGroup": field.denied_group.name if field.denied_group else "",
            "isDiagTable": field.is_diag_table,
            "file_settings": file_settings,
            "for_talon": field.for_talon,
            "sign_organization": field.sign_organization,
            "for_extract_card": field.for_extract_card,
            "for_med_certificate": field.for_med_certificate,
            "attached": field.attached or "",
            "layout_link_research_id": field.layout_link_research_id,
            "cdaOption": field.cda_option_id if field.cda_option_id else -1,
        }

    @staticmethod
    def serialize_group(group):
        fields = [TypeDocumentsSchema.serialize_field(field) for field in group.paraclinicinputfield_set.all() if field.field_type != LAYOUT_TEMPLATE_FIELD_TYPE]
        fields.sort(key=lambda row: row["order"])
        return {
            "pk": group.pk,
            "order": group.order,
            "title": group.title,
            "show_title": group.show_title,
            "hide": group.hide,
            "visibility": group.visibility or "",
            "fieldsInline": group.fields_inline,
            "fields": fields,
        }

    @staticmethod
    def dump_from_type(type_doc):
        from django.db.models import Prefetch

        from directory.models import ParaclinicInputField, ParaclinicInputGroups

        templates = type_doc.get_layout_templates() if type_doc else []
        if not templates:
            return None
        groups = []
        group_order = 0
        for template in templates:
            group_qs = (
                ParaclinicInputGroups.objects.filter(research=template)
                .order_by("order")
                .prefetch_related(
                    Prefetch(
                        "paraclinicinputfield_set",
                        queryset=ParaclinicInputField.objects.select_related("denied_group", "file_settings").order_by("order"),
                    )
                )
            )
            for group in group_qs:
                if group.hide:
                    continue
                serialized = TypeDocumentsSchema.serialize_group(group)
                if not serialized["fields"]:
                    continue
                serialized["order"] = group_order
                group_order += 1
                groups.append(serialized)
        first = templates[0]
        return {
            "pk": first.pk,
            "title": first.title,
            "wide_headers": any(bool(getattr(row, "wide_headers", False)) for row in templates),
            "layoutTemplateIds": [row.pk for row in templates],
            "groups": groups,
        }

    @staticmethod
    def get_or_create_for_type(type_doc):
        dumped = TypeDocumentsSchema.dump_from_type(type_doc)
        if not dumped:
            return None
        latest = TypeDocumentsSchema.objects.filter(type_document=type_doc).order_by("-created_at", "-pk").first()
        if latest and TypeDocumentsSchema._schema_key(latest.schema) == TypeDocumentsSchema._schema_key(dumped):
            return latest
        return TypeDocumentsSchema.objects.create(type_document=type_doc, schema=dumped)

    @staticmethod
    def sync_for_layout_template(template):
        if not template:
            return
        type_ids = TypeDocumentLayoutTemplate.objects.filter(layout_template=template).values_list("type_document_id", flat=True)
        qs = TypeDocuments.objects.filter(models.Q(pk__in=type_ids) | models.Q(layout_template=template)).distinct()
        for type_doc in qs:
            TypeDocumentsSchema.get_or_create_for_type(type_doc)


class Documents(models.Model):
    type_document = models.ForeignKey(TypeDocuments, db_index=True, default=None, blank=True, null=True, help_text="Тип документа", on_delete=models.SET_NULL)
    schema = models.ForeignKey(
        TypeDocumentsSchema,
        related_name="documents",
        db_index=True,
        default=None,
        blank=True,
        null=True,
        help_text="Снимок схемы шаблона",
        on_delete=models.PROTECT,
    )
    who_create = models.ForeignKey(DoctorProfile, db_index=True, default=None, blank=True, null=True, help_text="Создатель документа", on_delete=models.SET_NULL)
    create_at = models.DateTimeField(auto_now_add=True, help_text="Дата создания документа", db_index=True)
    time_registration = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Время регистрации")
    number_registration = models.CharField(max_length=20, blank=True, help_text="Регистрационный номер документа", db_index=True)
    is_registered = models.BooleanField(default=False, blank=True, help_text="Прошел регистрацию", db_index=True)
    need_approve = models.BooleanField(default=False, blank=True, help_text="Находится на согласовании", db_index=True)
    need_control = models.BooleanField(default=False, blank=True, help_text="Находится на контроле", db_index=True)
    total_approved = models.BooleanField(default=False, blank=True, help_text="Полностью согласован", db_index=True)
    total_completed = models.BooleanField(default=False, blank=True, help_text="Полностью завершен/снят с контроля", db_index=True)
    parent_document = models.ForeignKey("self", db_index=True, related_name="document_p", help_text="Документ основание", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    body_values = models.JSONField(default=dict, blank=True, help_text="Значения полей шаблона")
    time_confirm = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Время подтверждения")
    who_confirm = models.ForeignKey(
        DoctorProfile,
        related_name="document_who_confirm",
        db_index=True,
        default=None,
        blank=True,
        null=True,
        help_text="Кто подтвердил",
        on_delete=models.SET_NULL,
    )
    is_hidden = models.BooleanField(default=False, blank=True, db_index=True, help_text="Скрыт из списков")

    HIDDEN_DOCS_GROUP = "Скрытие документа"
    RESET_GROUP = "Сброс документов"
    HISTORY_GROUP = "История документа"
    LOG_CREATE = 260000
    LOG_SAVE = 260001
    LOG_CONFIRM = 260002
    LOG_RESET = 260003
    LOG_HIDE = 260004
    LOG_SHOW = 260005
    LOG_TYPES = (LOG_CREATE, LOG_SAVE, LOG_CONFIRM, LOG_RESET, LOG_HIDE, LOG_SHOW)

    class Meta:
        verbose_name = "Документ-экземпляр"
        verbose_name_plural = "Документы экземляров"

    def __str__(self):
        return f"{self.type_document}"

    def list_title(self, iss=None, topic=None):
        type_title = self.type_document.title if self.type_document else "Документ"
        fallback = self.number_registration or f"{type_title} №{self.pk}"
        is_saved = bool(self.time_confirm or (iss and (iss.time_confirmation or iss.time_save)))
        topic_text = "" if topic is None else str(topic).strip()
        if is_saved and topic_text:
            return topic_text
        return fallback

    @staticmethod
    def title_with_id(pk, title):
        marker = str(pk)
        text = (title or "").strip()
        suffix = f"№{marker}"
        if text.endswith(suffix):
            text = text[: -len(suffix)].rstrip()
        if text.startswith(f"{marker} ") or text == marker:
            return text
        return f"{marker} {text}" if text else marker

    @staticmethod
    def topic_cda_id():
        from laboratory.settings import CDA_TOPIC_ID_FOR_DOCUMENT_MANAGER

        raw = CDA_TOPIC_ID_FOR_DOCUMENT_MANAGER
        if raw in (None, "", -1, "-1"):
            return None
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return None
        return value if value > 0 else None

    @staticmethod
    def topic_from_research(research):
        topic_id = Documents.topic_cda_id()
        if not topic_id or not research:
            return ""
        for group in research.get("groups") or []:
            for field in group.get("fields") or []:
                cda = field.get("cdaOption")
                if cda in (None, "", -1, "-1"):
                    continue
                try:
                    if int(cda) != topic_id:
                        continue
                except (TypeError, ValueError):
                    continue
                value = (field.get("value") or "").strip()
                if value:
                    return value
        return ""

    @staticmethod
    def _topic_field_ids_from_schema(doc, topic_id):
        schema = getattr(doc, "schema", None)
        snapshot = getattr(schema, "schema", None) if schema else None
        if not isinstance(snapshot, dict):
            return []
        ids = []
        for group in snapshot.get("groups") or []:
            for field in group.get("fields") or []:
                cda = field.get("cdaOption")
                if cda in (None, "", -1, "-1"):
                    continue
                try:
                    if int(cda) != topic_id:
                        continue
                except (TypeError, ValueError):
                    continue
                pk = field.get("pk")
                if pk:
                    ids.append(pk)
        return ids

    @staticmethod
    def topics_for_documents(docs, iss_by_doc=None):
        from directory.models import ParaclinicInputField
        from directions.models import ParaclinicResult

        topic_id = Documents.topic_cda_id()
        if not topic_id or not docs:
            return {}
        iss_by_doc = iss_by_doc or {}
        topic_by_doc = {}
        field_ids = list(ParaclinicInputField.objects.filter(cda_option_id=topic_id).values_list("pk", flat=True))
        snapshot_field_ids_by_doc = {}
        for doc in docs:
            extra = Documents._topic_field_ids_from_schema(doc, topic_id)
            if extra:
                snapshot_field_ids_by_doc[doc.pk] = extra
                field_ids = list({*field_ids, *extra})
        iss_ids = [iss.pk for iss in iss_by_doc.values()]
        if field_ids and iss_ids:
            rows = ParaclinicResult.objects.filter(issledovaniye_id__in=iss_ids, field_id__in=field_ids).exclude(value="").select_related("issledovaniye")
            for row in rows:
                value = (row.value or "").strip()
                if value:
                    topic_by_doc.setdefault(row.issledovaniye.document_id, value)
        for doc in docs:
            if doc.pk in topic_by_doc:
                continue
            body = doc.body_values if isinstance(doc.body_values, dict) else {}
            ids = list(dict.fromkeys([*snapshot_field_ids_by_doc.get(doc.pk, []), *field_ids]))
            for field_id in ids:
                value = body.get(str(field_id), body.get(field_id))
                if value and str(value).strip():
                    topic_by_doc[doc.pk] = str(value).strip()
                    break
        return topic_by_doc

    def topic_value(self, iss=None, research=None):
        if research is not None:
            return Documents.topic_from_research(research)
        iss_by_doc = {self.pk: iss} if iss else {}
        return Documents.topics_for_documents([self], iss_by_doc).get(self.pk, "")

    @property
    def json(self):
        type_title = self.type_document.title if self.type_document else "Документ"
        group = self.type_document.group_document if self.type_document else None
        return {
            "id": self.id,
            "title": self.list_title(),
            "typeId": self.type_document_id,
            "typeTitle": type_title,
            "groupId": group.pk if group else None,
            "groupTitle": group.title if group else "",
            "confirmed": bool(self.time_confirm),
            "isHidden": self.is_hidden,
        }

    @classmethod
    def _who_group_names(cls, who, *group_names):
        names = [name for name in group_names if name]
        if not who or not names:
            return set()
        user = getattr(who, "user", None)
        if user and getattr(user, "is_superuser", False):
            return set(names)
        if not user:
            return set()
        return set(user.groups.filter(name__in=names).values_list("name", flat=True))

    @classmethod
    def can_view_all_hidden(cls, who):
        if not who:
            return False
        user = getattr(who, "user", None)
        if user and getattr(user, "is_superuser", False):
            return True
        return who.has_group(cls.HIDDEN_DOCS_GROUP)

    @classmethod
    def document_is_confirmed(cls, obj, iss=None):
        if obj.time_confirm:
            return True
        if iss is not None:
            return bool(iss.time_confirmation)
        from directions.models import Issledovaniya

        return Issledovaniya.objects.filter(document=obj, time_confirmation__isnull=False).exists()

    @classmethod
    def can_see_document(cls, obj, who):
        if not obj.is_hidden:
            return True
        return cls.can_view_all_hidden(who)

    @classmethod
    def can_set_hidden(cls, obj, who, confirmed=None):
        if not who:
            return False
        user = getattr(who, "user", None)
        if user and getattr(user, "is_superuser", False):
            return True
        if obj.who_create_id == getattr(who, "pk", None):
            if confirmed is None:
                confirmed = cls.document_is_confirmed(obj)
            if not confirmed:
                return True
        return who.has_group(cls.HIDDEN_DOCS_GROUP)

    @classmethod
    def can_reset_confirm(cls, who):
        if not who:
            return False
        user = getattr(who, "user", None)
        if user and getattr(user, "is_superuser", False):
            return True
        return who.has_group(cls.RESET_GROUP)

    @staticmethod
    def find_by_id(pk, who=None):
        try:
            pk = int(pk)
        except (TypeError, ValueError):
            return {"ok": False, "message": "Введите номер документа"}
        if pk <= 0:
            return {"ok": False, "message": "Введите номер документа"}
        obj = Documents.objects.select_related("type_document", "type_document__group_document").filter(pk=pk).first()
        if not obj or not Documents.can_see_document(obj, who):
            return {"ok": False, "message": "Документ не найден"}
        payload = obj.json
        payload["ok"] = True
        return payload

    @classmethod
    def log_action(cls, pk, log_type, who, extra=None):
        from slog.models import Log

        Log.log(str(pk), log_type, who, extra or {})

    @staticmethod
    def get_list(type_id=None, group_id=None, role_filter=None, who=None, hidden=False):
        qs = Documents.objects.select_related("type_document", "type_document__group_document", "schema").order_by("-pk")
        if role_filter == "toReview":
            if not who:
                return []
            qs = qs.filter(pk__in=DocumentReview.pending_document_ids(who))
        else:
            if type_id not in (None, "", -1, "-1"):
                qs = qs.filter(type_document_id=type_id)
            elif group_id in (-1, "-1"):
                qs = qs.filter(models.Q(type_document__isnull=True) | models.Q(type_document__group_document__isnull=True))
            elif group_id not in (None, "", 0, "0"):
                qs = qs.filter(type_document__group_document_id=group_id)
            if role_filter == "created" and who:
                qs = qs.filter(who_create=who)
        if hidden:
            if not Documents.can_view_all_hidden(who):
                return []
            qs = qs.filter(is_hidden=True)
        else:
            qs = qs.filter(is_hidden=False)
        docs = list(qs)
        if not docs:
            return []

        from directions.models import Issledovaniya

        iss_by_doc = {}
        for iss in Issledovaniya.objects.filter(document_id__in=[doc.pk for doc in docs]).order_by("pk"):
            iss_by_doc.setdefault(iss.document_id, iss)
        topic_by_doc = Documents.topics_for_documents(docs, iss_by_doc)

        result = []
        for doc in docs:
            payload = doc.json
            title = doc.list_title(iss_by_doc.get(doc.pk), topic_by_doc.get(doc.pk))
            if role_filter == "toReview":
                title = Documents.title_with_id(doc.pk, title)
            payload["title"] = title
            result.append(payload)
        return result

    @staticmethod
    def create_document(type_id, who_create):
        from directions.models import Issledovaniya

        if type_id in (None, "", -1, "-1"):
            return {"ok": False, "message": "Выберите вид документа"}
        type_doc = TypeDocuments.objects.filter(pk=type_id).first()
        if not type_doc:
            return {"ok": False, "message": "Вид документа не найден"}
        if not type_doc.can_create(who_create):
            return {"ok": False, "message": "Нет прав на создание этого вида документа"}
        with transaction.atomic():
            schema = TypeDocumentsSchema.get_or_create_for_type(type_doc)
            obj = Documents.objects.create(type_document=type_doc, who_create=who_create, body_values={}, schema=schema)
            templates = type_doc.get_layout_templates()
            Issledovaniya.objects.create(
                document=obj,
                research=templates[0] if templates else type_doc.layout_template,
                creator=who_create,
            )
        Documents.log_action(
            obj.pk,
            Documents.LOG_CREATE,
            who_create,
            {"title": obj.json["title"], "typeId": obj.type_document_id, "typeTitle": obj.type_document.title if obj.type_document else ""},
        )
        return {"ok": True, "id": obj.pk, "title": obj.json["title"]}

    def get_issledovaniye(self):
        from directions.models import Issledovaniya

        prefetched = getattr(self, "_prefetched_objects_cache", {}).get("issledovaniya_set")
        if prefetched is not None:
            iss = prefetched[0] if prefetched else None
        else:
            iss = Issledovaniya.objects.filter(document=self).only("pk", "time_confirmation", "document_id", "research_id").order_by("pk").first()
        if iss:
            return iss
        type_doc = self.type_document
        templates = type_doc.get_layout_templates() if type_doc else []
        return Issledovaniya.objects.create(
            document=self,
            research=templates[0] if templates else (type_doc.layout_template if type_doc else None),
            creator=self.who_create,
        )

    def _schema_snapshot(self):
        if self.schema_id:
            snapshot = getattr(self.schema, "schema", None)
            if isinstance(snapshot, dict) and snapshot.get("groups") is not None:
                return snapshot
        if not self.type_document_id:
            return None
        latest = TypeDocumentsSchema.objects.filter(type_document_id=self.type_document_id).order_by("-created_at", "-pk").only("pk", "schema").first()
        if latest and isinstance(latest.schema, dict) and latest.schema.get("groups") is not None:
            if not self.schema_id:
                Documents.objects.filter(pk=self.pk, schema_id__isnull=True).update(schema_id=latest.pk)
                self.schema_id = latest.pk
            return latest.schema
        return TypeDocumentsSchema.dump_from_type(self.type_document)

    def build_research(self, iss=None):
        snapshot = self._schema_snapshot()
        if not snapshot:
            return None
        return self._research_from_schema(snapshot, iss)

    def _research_from_schema(self, snapshot, iss=None):
        from directions.models import ParaclinicResult, ParaclinicResultFile

        saved = self.body_values if isinstance(self.body_values, dict) else {}
        result_by_field = {}
        files_by_result = {}
        if iss:
            rows = list(ParaclinicResult.objects.filter(issledovaniye_id=iss.pk).only("pk", "field_id", "value", "field_type"))
            result_by_field = {row.field_id: row for row in rows}
            type42_ids = set()
            for group in snapshot.get("groups") or []:
                for field in group.get("fields") or []:
                    if field.get("field_type") == 42:
                        type42_ids.add(field.get("pk"))
            result_pks = [result_by_field[field_id].pk for field_id in type42_ids if field_id in result_by_field]
            if result_pks:
                for row in ParaclinicResultFile.objects.filter(result_id__in=result_pks).order_by("pk"):
                    files_by_result.setdefault(row.result_id, []).append(row)
        confirmed = bool(iss.time_confirmation) if iss else False
        groups = []
        for group in snapshot.get("groups") or []:
            if group.get("hide"):
                continue
            g = {
                "pk": group.get("pk"),
                "order": group.get("order"),
                "title": group.get("title") if group.get("show_title") else "",
                "show_title": group.get("show_title"),
                "hide": group.get("hide"),
                "display_hidden": False,
                "fields": [],
                "visibility": group.get("visibility") or "",
                "fieldsInline": group.get("fieldsInline"),
            }
            for field in group.get("fields") or []:
                if field.get("hide") or field.get("field_type") == LAYOUT_TEMPLATE_FIELD_TYPE:
                    continue
                field_pk = field.get("pk")
                values_to_input = field.get("values_to_input") or []
                if not isinstance(values_to_input, list):
                    values_to_input = []
                result_field = result_by_field.get(field_pk)
                field_type = field.get("field_type") or 0
                if confirmed and result_field is not None and result_field.field_type is not None:
                    field_type = result_field.field_type
                if field.get("required") and field_type in [10, 12] and "- Не выбрано" not in values_to_input:
                    values_to_input = ["- Не выбрано", *values_to_input]
                default_value = field.get("default_value") or ""
                if field_type in [3, 11, 13, 14, 30, 42, 44, ADDRESSEE_FIELD_TYPE, MENTEE_FIELD_TYPE, MENTOR_FIELD_TYPE]:
                    default_value = ""
                key = str(field_pk)
                if result_field:
                    value = result_field.value
                elif key in saved:
                    value = saved[key]
                else:
                    value = saved.get(field_pk, default_value)
                if field_type == ADDRESSEE_FIELD_TYPE and not value:
                    value = "[]"
                file_settings = field.get("file_settings")
                files = []
                if field_type == 42:
                    value = ""
                    if result_field:
                        files = [ParaclinicResultFile.serialize(row) for row in files_by_result.get(result_field.pk, [])]
                g["fields"].append(
                    {
                        "pk": field_pk,
                        "order": field.get("order"),
                        "lines": field.get("lines"),
                        "title": field.get("short_title") or field.get("title") or "",
                        "hide": field.get("hide"),
                        "values_to_input": values_to_input,
                        "value": value if value is not None else "",
                        "field_type": field_type,
                        "can_edit": field.get("can_edit"),
                        "default_value": field.get("default_value") or "",
                        "visibility": field.get("visibility") or "",
                        "required": field.get("required"),
                        "helper": field.get("helper") or "",
                        "controlParam": field.get("controlParam") or "",
                        "not_edit": field.get("not_edit"),
                        "operator_enter_param": field.get("operator_enter_param"),
                        "deniedGroup": field.get("deniedGroup") or "",
                        "isDiagTable": field.get("isDiagTable"),
                        "file_settings": file_settings,
                        "files": files,
                        "cdaOption": field.get("cdaOption", -1),
                    }
                )
            if not g["fields"]:
                continue
            groups.append(g)
        return {
            "pk": snapshot.get("pk"),
            "title": snapshot.get("title"),
            "version": 0,
            "wide_headers": bool(snapshot.get("wide_headers")),
            "groups": groups,
            "is_gistology": False,
            "show_more_services": False,
        }

    @staticmethod
    def get_details(pk, who=None):
        from django.db.models import Prefetch
        from directions.models import Issledovaniya

        obj = (
            Documents.objects.select_related("schema", "type_document", "type_document__layout_template", "type_document__group_document")
            .prefetch_related(
                Prefetch(
                    "issledovaniya_set",
                    queryset=Issledovaniya.objects.only("pk", "time_confirmation", "document_id", "research_id").order_by("pk"),
                )
            )
            .filter(pk=pk)
            .first()
        )
        if not obj:
            return {"ok": False, "message": "Документ не найден"}
        group_names = Documents._who_group_names(who, Documents.HIDDEN_DOCS_GROUP, Documents.RESET_GROUP)
        if obj.is_hidden and Documents.HIDDEN_DOCS_GROUP not in group_names:
            return {"ok": False, "message": "Документ не найден"}
        iss = obj.get_issledovaniye()
        research = obj.build_research(iss)
        payload = obj.json
        payload["ok"] = True
        payload["issPk"] = iss.pk if iss else None
        payload["research"] = research
        payload["confirmed"] = bool(iss and iss.time_confirmation) or bool(obj.time_confirm)
        can_hide = Documents.HIDDEN_DOCS_GROUP in group_names
        if not can_hide and who and obj.who_create_id == getattr(who, "pk", None) and not payload["confirmed"]:
            can_hide = True
        payload["canHide"] = can_hide
        payload["canReset"] = Documents.RESET_GROUP in group_names
        payload["reviewedNow"] = DocumentReview.mark_opened(obj, who, iss=iss) if payload["confirmed"] else False
        type_doc = obj.type_document.title if obj.type_document else ""
        DocumentRecent.remember(who, obj, topic=obj.topic_value(iss, research=research), type_doc=type_doc)
        return payload

    @staticmethod
    def save_paraclinic_result(iss_pk, research, with_confirm, visibility_state, who, request_files=None):
        from django.utils import timezone

        from directory.models import ParaclinicInputField
        from directions.models import Issledovaniya, ParaclinicResult, ParaclinicResultFile

        iss = Issledovaniya.objects.filter(pk=iss_pk, document__isnull=False).select_related("document", "research").first()
        if not iss or not iss.document:
            return {"ok": False, "message": "Исследование не найдено"}
        if not Documents.can_see_document(iss.document, who):
            return {"ok": False, "message": "Документ не найден"}
        if iss.time_confirmation or iss.document.time_confirm:
            return {"ok": False, "message": "Документ подтверждён"}
        v_g = (visibility_state or {}).get("groups") or {}
        v_f = (visibility_state or {}).get("fields") or {}
        groups = (research or {}).get("groups") or []
        files_by_field = {}
        document = iss.document
        body_values = dict(document.body_values) if isinstance(document.body_values, dict) else {}
        addressee_ids = []
        addressee_seen = set()
        has_addressee_field = False
        with transaction.atomic():
            for group in groups:
                group_pk = group.get("pk")
                if not v_g.get(str(group_pk), True):
                    ParaclinicResult.objects.filter(issledovaniye=iss, field__group__pk=group_pk).delete()
                    for field in group.get("fields") or []:
                        field_pk = field.get("pk")
                        if field_pk:
                            body_values.pop(str(field_pk), None)
                    continue
                for field in group.get("fields") or []:
                    field_pk = field.get("pk")
                    if not field_pk:
                        continue
                    if not v_f.get(str(field_pk), True):
                        ParaclinicResult.objects.filter(issledovaniye=iss, field__pk=field_pk).delete()
                        body_values.pop(str(field_pk), None)
                        continue
                    value = field.get("value")
                    stored_value = "" if not value else value
                    payload_field_type = field.get("field_type")
                    f = ParaclinicInputField.objects.filter(pk=field_pk).first()
                    if not f or f.field_type == 21:
                        if payload_field_type != 21:
                            body_values[str(field_pk)] = stored_value
                        continue
                    body_values[str(field_pk)] = stored_value
                    f_result = ParaclinicResult.objects.filter(issledovaniye=iss, field=f).first()
                    if not f_result:
                        f_result = ParaclinicResult(issledovaniye=iss, field=f, value="")
                    f_result.value = stored_value
                    f_result.field_type = payload_field_type if payload_field_type is not None else f.field_type
                    field_type = f_result.field_type
                    if field_type == ADDRESSEE_FIELD_TYPE:
                        has_addressee_field = True
                        if isinstance(stored_value, (dict, list)):
                            stored_value = json.dumps(stored_value)
                            f_result.value = stored_value
                            body_values[str(field_pk)] = stored_value
                        for doctor_id in DocumentReview.parse_addressee_ids(value):
                            if doctor_id not in addressee_seen:
                                addressee_seen.add(doctor_id)
                                addressee_ids.append(doctor_id)
                    if field_type in [27, 28, 29, 32, 33, 34, 35, 44, ADDRESSEE_FIELD_TYPE, MENTEE_FIELD_TYPE, MENTOR_FIELD_TYPE]:
                        if isinstance(value, (dict, list)):
                            val = value
                        else:
                            try:
                                val = json.loads(value)
                            except Exception:
                                val = []
                        f_result.value_json = val
                    f_result.save()
                    if field_type == 42:
                        files_by_field[field_pk] = ParaclinicResultFile.sync_field_files(
                            f_result=f_result,
                            payload_files=field.get("files") or [],
                            uploaded_files=request_files or {},
                            field_pk=field_pk,
                        )
            iss.doc_save = who
            iss.time_save = timezone.now()
            document.body_values = body_values
            update_fields = ["body_values"]
            if with_confirm:
                now = timezone.now()
                iss.doc_confirmation = who
                iss.time_confirmation = now
                document.time_confirm = now
                document.who_confirm = who
                update_fields.extend(["time_confirm", "who_confirm"])
            document.save(update_fields=update_fields)
            iss.save()
            if has_addressee_field:
                DocumentReview.sync_for_document(document, addressee_ids)
            DocumentRecent.objects.filter(document=document).update(topic=document.topic_value(iss, research=research))
        Documents.log_action(
            document.pk,
            Documents.LOG_CONFIRM if with_confirm else Documents.LOG_SAVE,
            who,
            {
                "title": document.json.get("title") if isinstance(document.json, dict) else "",
                "typeId": document.type_document_id,
                "typeTitle": document.type_document.title if document.type_document else "",
                "issPk": iss.pk,
                "confirmed": bool(iss.time_confirmation),
            },
        )
        return {
            "ok": True,
            "id": iss.document_id,
            "issPk": iss.pk,
            "confirmed": bool(iss.time_confirmation),
            "files_by_field": files_by_field,
        }

    @staticmethod
    def confirm_reset(pk, who=None):
        from directions.models import Issledovaniya

        obj = Documents.objects.filter(pk=pk).first()
        if not obj:
            return {"ok": False, "message": "Документ не найден"}
        if not Documents.can_reset_confirm(who):
            return {"ok": False, "message": "Нет прав"}
        if not Documents.can_see_document(obj, who):
            return {"ok": False, "message": "Документ не найден"}
        iss = Issledovaniya.objects.filter(document=obj).order_by("pk").first()
        if (not iss or not iss.time_confirmation) and not obj.time_confirm:
            return {"ok": False, "message": "Документ не подтверждён"}
        if iss:
            iss.time_confirmation = None
            iss.doc_confirmation = None
            iss.executor_confirmation = None
            iss.save(update_fields=["time_confirmation", "doc_confirmation", "executor_confirmation"])
        obj.time_confirm = None
        obj.who_confirm = None
        obj.save(update_fields=["time_confirm", "who_confirm"])
        Documents.log_action(
            obj.pk,
            Documents.LOG_RESET,
            who,
            {
                "title": obj.json.get("title") if isinstance(obj.json, dict) else "",
                "typeId": obj.type_document_id,
                "typeTitle": obj.type_document.title if obj.type_document else "",
            },
        )
        return {"ok": True, "id": obj.pk, "confirmed": False}

    @staticmethod
    def set_hidden(pk, hidden, who):
        obj = Documents.objects.filter(pk=pk).first()
        if not obj:
            return {"ok": False, "message": "Документ не найден"}
        if not Documents.can_set_hidden(obj, who):
            return {"ok": False, "message": "Нет прав"}
        obj.is_hidden = bool(hidden)
        obj.save(update_fields=["is_hidden"])
        Documents.log_action(
            obj.pk,
            Documents.LOG_HIDE if obj.is_hidden else Documents.LOG_SHOW,
            who,
            {
                "title": obj.json.get("title") if isinstance(obj.json, dict) else "",
                "typeId": obj.type_document_id,
                "typeTitle": obj.type_document.title if obj.type_document else "",
                "isHidden": obj.is_hidden,
            },
        )
        return {"ok": True, "id": obj.pk, "isHidden": obj.is_hidden}

    @classmethod
    def get_history_for_document(cls, pk):
        from laboratory.utils import strdatetime
        from slog.models import Log

        try:
            pk = int(pk)
        except (TypeError, ValueError):
            return []
        if pk < 1 or not cls.objects.filter(pk=pk).exists():
            return []

        body_labels = {
            "title": "Заголовок",
            "typeId": "Код вида",
            "typeTitle": "Вид",
            "issPk": "Исследование",
            "confirmed": "Подтверждён",
            "isHidden": "Скрыт",
        }
        yesno = {True: "да", False: "нет"}
        events = []
        logs = Log.objects.filter(key=str(pk), type__in=cls.LOG_TYPES).select_related("user__user", "user__podrazdeleniye").order_by("time", "pk")
        for lg in logs:
            event = [["title", f"{strdatetime(lg.time)} {lg.get_type_display()}"]]
            if lg.user:
                podr = lg.user.podrazdeleniye.title if lg.user.podrazdeleniye else ""
                username = lg.user.user.username if lg.user.user else ""
                event.append(["Пользователь", f"{lg.user.fio}, {username}, {podr}"])
            if lg.body:
                try:
                    parsed = json.loads(lg.body)
                except Exception:
                    parsed = None
                if isinstance(parsed, dict):
                    for key, value in parsed.items():
                        if isinstance(value, (dict, list)):
                            event.append(["json_data", json.dumps(value, ensure_ascii=False)])
                            continue
                        if isinstance(value, bool):
                            value = yesno[value]
                        if value in ("", None):
                            continue
                        event.append([body_labels.get(key, key), str(value)])
                elif parsed is not None:
                    event.append(["json_data", lg.body])
                else:
                    event.append(["Данные", lg.body])
            events.append(event)
        return [{"type": f"Документ №{pk}", "events": events}]


class DocumentEmployeeApprove(models.Model):
    document = models.ForeignKey(Documents, db_index=True, on_delete=models.CASCADE)
    employee = models.ForeignKey(DoctorProfile, related_name="employee_approve", db_index=True, default=None, blank=True, null=True, help_text="Согласующий", on_delete=models.SET_NULL)
    time_approve = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Время согласования исполнителем")
    create_at_approve = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Время запроса согласования")
    who_create = models.ForeignKey(
        DoctorProfile, related_name="who_create_to_approve", db_index=True, default=None, blank=True, null=True, help_text="кто запросил согласование", on_delete=models.SET_NULL
    )
    is_cancel = models.BooleanField(default=True, blank=True, db_index=True)
    note_cancel = models.CharField(max_length=130, blank=True, help_text="Причина отмены")

    class Meta:
        verbose_name = "Согласование документа"
        verbose_name_plural = "Согласования документов"

    def __str__(self):
        return f"{self.document} {self.employee} {self.time_approve} {self.is_cancel}"


class DocumentResolution(models.Model):
    document = models.ForeignKey(Documents, db_index=True, on_delete=models.CASCADE)
    employee = models.ForeignKey(DoctorProfile, related_name="employee_resolution", db_index=True, default=None, blank=True, null=True, help_text="Исполнитель", on_delete=models.SET_NULL)
    time_resolution = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Время создания резолюции")
    who_create = models.ForeignKey(
        DoctorProfile, related_name="who_create_resolution", db_index=True, default=None, blank=True, null=True, help_text="Кто создал резолюцию", on_delete=models.SET_NULL
    )
    is_cancel = models.BooleanField(default=True, blank=True, db_index=True)
    note_cancel = models.CharField(max_length=128, blank=True, help_text="Причина отмены")
    note_resolution = models.CharField(max_length=255, blank=True, help_text="Содержание резолюции")
    parent_resolution = models.ForeignKey("self", db_index=True, related_name="resolution_p", help_text="Резолюция основание", blank=True, null=True, default=None, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Резолюция документа"
        verbose_name_plural = "Резолюции документов"

    def __str__(self):
        return f"{self.document} {self.employee} {self.time_resolution} {self.is_cancel}"


class DocumentControl(models.Model):
    document = models.ForeignKey(Documents, db_index=True, on_delete=models.CASCADE)
    time_control = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Дата контроля")
    resolution = models.ForeignKey(DocumentResolution, db_index=True, on_delete=models.CASCADE, help_text="Резолюция")
    is_completed = models.BooleanField(default=False, blank=True, db_index=True, help_text="Выполнена резолюция")

    class Meta:
        verbose_name = "Контроль документа"
        verbose_name_plural = "Контроли документов"

    def __str__(self):
        return f"{self.document} {self.document} {self.time_control}"


class DocumentReview(models.Model):
    document = models.ForeignKey(Documents, db_index=True, on_delete=models.CASCADE)
    time_review = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Дата ознакомления")
    doctor_review = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, help_text="Кто  должен ознакомлен", on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Ознакомление документа"
        verbose_name_plural = "Ознакомления документов"

    def __str__(self):
        return f"{self.document} {self.doctor_review} {self.time_review}"

    @classmethod
    def pending_qs(cls, who):
        qs = cls.objects.filter(time_review__isnull=True, document__is_hidden=False)
        if who:
            qs = qs.filter(doctor_review=who)
        else:
            qs = qs.none()
        return qs

    @classmethod
    def pending_document_ids(cls, who):
        return cls.pending_qs(who).values("document_id")

    @classmethod
    def pending_count(cls, who):
        if not who:
            return 0
        return cls.pending_qs(who).values("document_id").distinct().count()

    @classmethod
    def mark_opened(cls, document, who, iss=None):
        if not document or not who:
            return False
        if not document.time_confirm:
            if iss is None:
                iss = document.get_issledovaniye()
            if not iss or not iss.time_confirmation:
                return False
        from django.utils import timezone

        updated = cls.objects.filter(document=document, doctor_review=who, time_review__isnull=True).update(time_review=timezone.now())
        return updated > 0

    @classmethod
    def parse_addressee_ids(cls, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except Exception:
                value = []
        if not isinstance(value, list):
            return []
        ids = []
        seen = set()
        for item in value:
            raw = item.get("id") if isinstance(item, dict) else item
            try:
                doctor_id = int(raw)
            except (TypeError, ValueError):
                continue
            if doctor_id < 1 or doctor_id in seen:
                continue
            seen.add(doctor_id)
            ids.append(doctor_id)
        return ids

    @classmethod
    def collect_ids_from_research(cls, research):
        ids = []
        seen = set()
        for group in (research or {}).get("groups") or []:
            for field in group.get("fields") or []:
                field_type = field.get("field_type")
                if field_type != ADDRESSEE_FIELD_TYPE:
                    continue
                for doctor_id in cls.parse_addressee_ids(field.get("value")):
                    if doctor_id in seen:
                        continue
                    seen.add(doctor_id)
                    ids.append(doctor_id)
        return ids

    @classmethod
    def sync_for_document(cls, document, doctor_ids):
        wanted = set(doctor_ids or [])
        if wanted:
            wanted = set(DoctorProfile.objects.filter(pk__in=wanted).values_list("pk", flat=True))
        existing = list(cls.objects.filter(document=document))
        keep = set()
        to_delete = []
        for row in existing:
            if row.doctor_review_id and row.doctor_review_id in wanted:
                keep.add(row.doctor_review_id)
            else:
                to_delete.append(row.pk)
        if to_delete:
            cls.objects.filter(pk__in=to_delete).delete()
        cls.objects.bulk_create([cls(document=document, doctor_review_id=doctor_id) for doctor_id in wanted if doctor_id not in keep])

    @classmethod
    def sync_from_research(cls, document, research):
        cls.sync_for_document(document, cls.collect_ids_from_research(research))


class DocumentRecent(models.Model):
    PAGE_SIZE = 50
    MAX_ITEMS = 200

    doctor = models.ForeignKey(DoctorProfile, related_name="document_recents", on_delete=models.CASCADE, help_text="Пользователь")
    document = models.ForeignKey(Documents, related_name="recent_opens", on_delete=models.CASCADE, help_text="Документ")
    topic = models.CharField(max_length=255, blank=True, default="", help_text="Тема документа")
    type_doc = models.CharField(max_length=128, blank=True, default="", help_text="Вид документа")
    opened_at = models.DateTimeField(db_index=True, help_text="Дата и время последнего открытия")

    class Meta:
        verbose_name = "Последний документ"
        verbose_name_plural = "Последние документы"
        unique_together = ("doctor", "document")
        indexes = (models.Index(fields=("doctor", "-opened_at")),)
        ordering = ("-opened_at", "-pk")

    def __str__(self):
        return f"{self.doctor_id} {self.document_id} {self.opened_at}"

    @classmethod
    def remember(cls, who, document, topic="", type_doc=""):
        if not who or not document:
            return
        from django.utils import timezone

        defaults = {
            "topic": topic or "",
            "type_doc": type_doc or "",
            "opened_at": timezone.now(),
        }
        if cls.objects.filter(doctor=who, document=document).update(**defaults):
            return
        try:
            cls.objects.create(doctor=who, document=document, **defaults)
        except IntegrityError:
            cls.objects.filter(doctor=who, document=document).update(**defaults)
            return
        extra_ids = list(cls.objects.filter(doctor=who).order_by("-opened_at", "-pk").values_list("pk", flat=True)[cls.MAX_ITEMS :])
        if extra_ids:
            cls.objects.filter(pk__in=extra_ids).delete()

    @classmethod
    def get_page(cls, who, page=1, page_size=None):
        if not who:
            return {"result": [], "page": 1, "pageSize": cls.PAGE_SIZE, "hasMore": False}
        try:
            page = max(int(page or 1), 1)
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = max(int(page_size or cls.PAGE_SIZE), 1)
        except (TypeError, ValueError):
            page_size = cls.PAGE_SIZE
        qs = (
            cls.objects.filter(doctor=who, document__is_hidden=False, document__time_confirm__isnull=False)
            .select_related("document", "document__type_document", "document__schema")
            .order_by("-opened_at", "-pk")
        )
        offset = (page - 1) * page_size
        rows = list(qs[offset : offset + page_size + 1])
        has_more = len(rows) > page_size
        rows = rows[:page_size]
        from directions.models import Issledovaniya

        docs = [row.document for row in rows]
        iss_by_doc = {}
        if docs:
            for iss in Issledovaniya.objects.filter(document_id__in=[doc.pk for doc in docs]).order_by("pk"):
                iss_by_doc.setdefault(iss.document_id, iss)
        live_topics = Documents.topics_for_documents(docs, iss_by_doc)
        result = []
        for row in rows:
            topic = (live_topics.get(row.document_id) or row.topic or "").strip()
            type_doc = (row.type_doc or "").strip()
            if not type_doc and row.document.type_document:
                type_doc = row.document.type_document.title
            title = " ".join(part for part in (topic, type_doc) if part)
            result.append(
                {
                    "id": row.document_id,
                    "title": Documents.title_with_id(row.document_id, title),
                    "topic": topic,
                    "typeDoc": type_doc,
                }
            )
        return {
            "result": result,
            "page": page,
            "pageSize": page_size,
            "hasMore": has_more,
        }


class DocumentResult(models.Model):
    document = models.ForeignKey(Documents, db_index=True, default=None, blank=True, null=True, help_text="Тип документа", on_delete=models.SET_NULL)
    create_at = models.DateTimeField(auto_now_add=True, help_text="Дата создания/изменения", db_index=True)
    who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, help_text="Создатель", on_delete=models.SET_NULL)
    value = models.TextField(null=True, blank=True, help_text="Значение")
    document_field = models.ForeignKey(DocumentFields, db_index=True, default=None, blank=True, null=True, help_text="поле документа", on_delete=models.SET_NULL)
    field_type = models.SmallIntegerField(default=None, blank=True, choices=DocumentFields.TYPES, null=True)
    meta_document_field = models.ForeignKey(MetaFieldsForAllTypeDocuments, db_index=True, default=None, blank=True, null=True, help_text="поле документа", on_delete=models.SET_NULL)
    meta_field_type = models.SmallIntegerField(default=None, blank=True, choices=MetaFieldsForAllTypeDocuments.TYPES, null=True)

    class Meta:
        verbose_name = "Реквизит для документа"
        verbose_name_plural = "Реквизит для документов"

    def __str__(self):
        return f"{self.document}"


def get_file_path(instance: "DocumentFiles", filename):
    return os.path.join("document_files", str(instance.document.pk), str(uuid.uuid4()), filename)


class DocumentFiles(models.Model):
    document = models.ForeignKey(Documents, db_index=True, on_delete=models.CASCADE)
    uploaded_file = models.FileField(upload_to=get_file_path, blank=True, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    type_file = models.CharField(max_length=16, blank=True, help_text="Тип документа")
    who_add_files = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="document_who_add_files", help_text="Создатель направления", on_delete=models.SET_NULL)
    comment = models.CharField(max_length=130, blank=True, help_text="Комментарий")

    class Meta:
        verbose_name = "Файл на документ"
        verbose_name_plural = "Файлы на документы"
