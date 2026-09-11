import os
import uuid

import simplejson as json
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction

from hospitals.models import Hospitals
from podrazdeleniya.models import Podrazdeleniya
from users.models import DoctorProfile


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

    @property
    def json(self):
        return {
            "id": self.id,
            "title": self.title or "",
            "code": self.code or "",
            "groupId": self.group_document_id,
            "groupTitle": self.group_document.title if self.group_document else "",
            "layoutTemplateId": self.layout_template_id,
        }

    @staticmethod
    def get_list(group_id=None):
        qs = TypeDocuments.objects.select_related("group_document").all().order_by("title", "pk")
        if group_id in (-1, "-1"):
            qs = qs.filter(group_document__isnull=True)
        elif group_id not in (None, "", 0, "0"):
            qs = qs.filter(group_document_id=group_id)
        return [row.json for row in qs]

    @staticmethod
    def save_type(pk, title, group_id=None, code="", layout_template_id=None):
        from directory.models import Researches

        title = (title or "").strip()
        if not title:
            return {"ok": False, "message": "Укажите название"}
        group = None
        if group_id not in (None, "", -1, "-1"):
            group = GroupDocuments.objects.filter(pk=group_id).first()
            if not group:
                return {"ok": False, "message": "Группа не найдена"}
        layout_template = None
        if layout_template_id not in (None, "", -1, "-1"):
            layout_template = Researches.objects.filter(pk=layout_template_id, is_layout_template=True).first()
            if not layout_template:
                return {"ok": False, "message": "Шаблон не найден"}
        if pk in (None, -1, "-1"):
            obj = TypeDocuments(title=title, group_document=group, code=code or "", layout_template=layout_template)
        else:
            obj = TypeDocuments.objects.filter(pk=pk).first()
            if not obj:
                return {"ok": False, "message": "Вид документа не найден"}
            obj.title = title
            obj.group_document = group
            obj.code = code or ""
            obj.layout_template = layout_template
        obj.save()
        if obj.layout_template:
            TypeDocumentsSchema.get_or_create_for_type(obj)
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
        }

    @staticmethod
    def serialize_group(group):
        fields = [TypeDocumentsSchema.serialize_field(field) for field in group.paraclinicinputfield_set.all()]
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

        template = type_doc.layout_template if type_doc else None
        if not template:
            return None
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
        return {
            "pk": template.pk,
            "title": template.title,
            "wide_headers": bool(getattr(template, "wide_headers", False)),
            "groups": [TypeDocumentsSchema.serialize_group(group) for group in group_qs],
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
        for type_doc in TypeDocuments.objects.filter(layout_template=template):
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

    class Meta:
        verbose_name = "Документ-экземпляр"
        verbose_name_plural = "Документы экземляров"

    def __str__(self):
        return f"{self.type_document}"

    @property
    def json(self):
        type_title = self.type_document.title if self.type_document else "Документ"
        title = self.number_registration or f"{type_title} №{self.pk}"
        group = self.type_document.group_document if self.type_document else None
        return {
            "id": self.id,
            "title": title,
            "typeId": self.type_document_id,
            "typeTitle": type_title,
            "groupId": group.pk if group else None,
            "groupTitle": group.title if group else "",
            "confirmed": bool(self.time_confirm),
        }

    @staticmethod
    def get_list(type_id=None, group_id=None, role_filter=None, who=None):
        qs = Documents.objects.select_related("type_document", "type_document__group_document").order_by("-pk")
        if type_id not in (None, "", -1, "-1"):
            qs = qs.filter(type_document_id=type_id)
        elif group_id in (-1, "-1"):
            qs = qs.filter(models.Q(type_document__isnull=True) | models.Q(type_document__group_document__isnull=True))
        elif group_id not in (None, "", 0, "0"):
            qs = qs.filter(type_document__group_document_id=group_id)
        if role_filter == "created" and who:
            qs = qs.filter(who_create=who)
        return [row.json for row in qs]

    @staticmethod
    def create_document(type_id, who_create):
        from directions.models import Issledovaniya

        if type_id in (None, "", -1, "-1"):
            return {"ok": False, "message": "Выберите вид документа"}
        type_doc = TypeDocuments.objects.filter(pk=type_id).first()
        if not type_doc:
            return {"ok": False, "message": "Вид документа не найден"}
        with transaction.atomic():
            schema = TypeDocumentsSchema.get_or_create_for_type(type_doc)
            obj = Documents.objects.create(type_document=type_doc, who_create=who_create, body_values={}, schema=schema)
            Issledovaniya.objects.create(
                document=obj,
                research=type_doc.layout_template,
                creator=who_create,
            )
        return {"ok": True, "id": obj.pk, "title": obj.json["title"]}

    def get_issledovaniye(self):
        from directions.models import Issledovaniya

        iss = Issledovaniya.objects.filter(document=self).order_by("pk").first()
        if iss:
            return iss
        type_doc = self.type_document
        return Issledovaniya.objects.create(
            document=self,
            research=type_doc.layout_template if type_doc else None,
            creator=self.who_create,
        )

    def build_research(self, iss=None):
        snapshot = None
        if self.schema_id and isinstance(getattr(self.schema, "schema", None), dict) and self.schema.schema.get("groups") is not None:
            snapshot = self.schema.schema
        else:
            snapshot = TypeDocumentsSchema.dump_from_type(self.type_document)
        if not snapshot:
            return None
        return self._research_from_schema(snapshot, iss)

    def _research_from_schema(self, snapshot, iss=None):
        from directions.models import ParaclinicResult, ParaclinicResultFile

        saved = self.body_values if isinstance(self.body_values, dict) else {}
        result_fields = {}
        if iss:
            result_fields = {
                row.field_id: row
                for row in ParaclinicResult.objects.filter(issledovaniye=iss).select_related("field").prefetch_related("files")
            }
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
                if field.get("hide"):
                    continue
                field_pk = field.get("pk")
                values_to_input = field.get("values_to_input") or []
                if not isinstance(values_to_input, list):
                    values_to_input = []
                result_field = result_fields.get(field_pk)
                field_type = field.get("field_type") or 0
                if result_field:
                    field_type = result_field.get_field_type(default_field_type=field_type, is_confirmed_strict=confirmed)
                if field.get("required") and field_type in [10, 12] and "- Не выбрано" not in values_to_input:
                    values_to_input = ["- Не выбрано", *values_to_input]
                default_value = field.get("default_value") or ""
                if field_type in [3, 11, 13, 14, 30, 42, 44]:
                    default_value = ""
                key = str(field_pk)
                if result_field:
                    value = result_field.value
                elif key in saved:
                    value = saved[key]
                else:
                    value = saved.get(field_pk, default_value)
                file_settings = field.get("file_settings")
                files = []
                if field_type == 42:
                    value = ""
                    if result_field:
                        files = [ParaclinicResultFile.serialize(row) for row in result_field.files.all()]
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
                    }
                )
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
    def get_details(pk):
        obj = Documents.objects.select_related("schema", "type_document", "type_document__layout_template").filter(pk=pk).first()
        if not obj:
            return {"ok": False, "message": "Документ не найден"}
        iss = obj.get_issledovaniye()
        payload = obj.json
        payload["ok"] = True
        payload["issPk"] = iss.pk if iss else None
        payload["research"] = obj.build_research(iss)
        payload["confirmed"] = bool(iss and iss.time_confirmation) or bool(obj.time_confirm)
        return payload

    @staticmethod
    def save_paraclinic_result(iss_pk, research, with_confirm, visibility_state, who, request_files=None):
        from django.utils import timezone

        from directory.models import ParaclinicInputField
        from directions.models import Issledovaniya, ParaclinicResult, ParaclinicResultFile

        iss = Issledovaniya.objects.filter(pk=iss_pk, document__isnull=False).select_related("document", "research").first()
        if not iss or not iss.document:
            return {"ok": False, "message": "Исследование не найдено"}
        if iss.time_confirmation or iss.document.time_confirm:
            return {"ok": False, "message": "Документ подтверждён"}
        v_g = (visibility_state or {}).get("groups") or {}
        v_f = (visibility_state or {}).get("fields") or {}
        groups = (research or {}).get("groups") or []
        files_by_field = {}
        document = iss.document
        body_values = dict(document.body_values) if isinstance(document.body_values, dict) else {}
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
                    if field_type in [27, 28, 29, 32, 33, 34, 35, 44]:
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
        return {
            "ok": True,
            "id": iss.document_id,
            "issPk": iss.pk,
            "confirmed": bool(iss.time_confirmation),
            "files_by_field": files_by_field,
        }

    @staticmethod
    def confirm_reset(pk):
        from directions.models import Issledovaniya

        obj = Documents.objects.filter(pk=pk).first()
        if not obj:
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
        return {"ok": True, "id": obj.pk, "confirmed": False}


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
