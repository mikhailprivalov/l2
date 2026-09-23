import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Max

from directory.models import ParaclinicInputField, ParaclinicInputFieldFileSettings, ParaclinicInputGroups, Researches


def parse_research_pks(raw):
    text = str(raw or "").strip()
    if not text:
        raise CommandError("Не указаны id услуг")
    pks = []
    seen = set()
    for item in text.split(","):
        value = item.strip()
        if not value:
            continue
        if not value.isdigit():
            raise CommandError(f"Некорректный id услуги: {value}")
        pk = int(value)
        if pk not in seen:
            seen.add(pk)
            pks.append(pk)
    if not pks:
        raise CommandError("Не указаны id услуг")
    return pks


def load_groups(path):
    """
    Same JSON as UI «Экспорт группы» / «Загрузить группу»:
    {"groups": [{title, show_title, order, hide, fields, fieldsInline, cdaOption, visibility, ...}]}
    """
    try:
        with open(path, encoding="utf-8") as source:
            data = json.load(source)
    except FileNotFoundError:
        raise CommandError(f"Файл не найден: {path}")
    except json.JSONDecodeError as exc:
        raise CommandError(f"Некорректный JSON: {exc}")

    if isinstance(data, list):
        groups = data
    elif isinstance(data, dict):
        groups = data.get("groups")
        if groups is None:
            groups = data.get("paraclinic_input_groups")
    else:
        groups = None

    if not isinstance(groups, list) or not groups:
        raise CommandError("JSON должен быть объектом с ключом groups (как «Экспорт группы») или списком групп")

    for group in groups:
        if not isinstance(group, dict):
            raise CommandError("Группа в JSON должна быть объектом")
        if "fields" not in group:
            raise CommandError("В файле не найдены поля ввода")
        if not isinstance(group["fields"], list):
            raise CommandError("Поля группы должны быть списком")

    return groups


def _optional_id(value):
    if value in (None, "", -1, "-1", 0, "0"):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _templates(value):
    if value is None or value == "":
        return "[]"
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if not isinstance(parsed, list):
                return "[]"
            return value
        except json.JSONDecodeError:
            return "[]"
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    return "[]"


def _next_group_order(research):
    current = ParaclinicInputGroups.objects.filter(research=research).aggregate(m=Max("order"))["m"]
    return (current or 0) + 1


def _add_group(research, group_settings):
    """Mirror ParaclinicResearchEditor.add_group + add_field, then persist like researches_update for pk=-1."""
    new_group = ParaclinicInputGroups(
        title=group_settings.get("title") or "",
        show_title=True if group_settings.get("show_title") is None else bool(group_settings.get("show_title")),
        research=research,
        order=_next_group_order(research),
        hide=bool(group_settings.get("hide") or False),
        visibility=group_settings.get("visibility") or "",
        fields_inline=bool(group_settings.get("fieldsInline") or False),
        cda_option_id=_optional_id(group_settings.get("cdaOption")),
    )
    new_group.save()

    fields_created = 0
    for field in group_settings.get("fields") or []:
        if not isinstance(field, dict):
            raise CommandError(f"Поле группы «{new_group.title}» должно быть объектом")
        new_field = ParaclinicInputField(
            title=field.get("title") or "",
            short_title=field.get("short_title") or "",
            group=new_group,
            order=field.get("order") if field.get("order") is not None else 0,
            default_value=field.get("default_value") or "",
            lines=field.get("lines") if field.get("lines") is not None else 3,
            field_type=field.get("field_type") if field.get("field_type") is not None else 0,
            for_extract_card=bool(field.get("for_extract_card") or False),
            for_talon=bool(field.get("for_talon") or False),
            for_med_certificate=bool(field.get("for_med_certificate") or False),
            operator_enter_param=bool(field.get("operator_enter_param") or False),
            is_diag_table=bool(field.get("is_diag_table") or False),
            not_edit=bool(field.get("not_edit") or False),
            required=bool(field.get("required") or False),
            visibility=field.get("visibility") or "",
            sign_organization=bool(field.get("sign_organization") or False),
            helper=field.get("helper") or "",
            can_edit_computed=bool(field.get("can_edit") or False),
            control_param=field.get("controlParam") or "",
            attached=field.get("attached") or "",
            input_templates=_templates(field.get("input_templates")),
            patient_control_param_id=_optional_id(field.get("patientControlParam")),
            cda_option_id=_optional_id(field.get("cdaOption")),
            statistic_pattern_param_id=_optional_id(field.get("patternParam")),
            hide=bool(field.get("hide") or False),
        )
        new_field.save()
        file_settings = field.get("file_settings")
        if new_field.field_type == 42 and isinstance(file_settings, dict):
            ParaclinicInputFieldFileSettings.update_file_field_settings(new_field, file_settings)
        fields_created += 1

    return new_group, fields_created


class Command(BaseCommand):
    help = "Загрузить группу(ы) из JSON (как «Загрузить группу») в услуги по pk"

    def add_arguments(self, parser):
        parser.add_argument("research_pks", type=str, help='pk услуг через запятую, например "12,34"')
        parser.add_argument("path", type=str, help="JSON из «Экспорт группы» / «Экспорт исследования»")

    def handle(self, *args, **kwargs):
        pks = parse_research_pks(kwargs["research_pks"])
        groups = load_groups(kwargs["path"])
        researches = list(Researches.objects.filter(pk__in=pks))
        found = {research.pk for research in researches}
        missing = [pk for pk in pks if pk not in found]
        if missing:
            raise CommandError("Услуги не найдены: " + ", ".join(str(pk) for pk in missing))
        researches.sort(key=lambda research: pks.index(research.pk))

        created_groups = 0
        created_fields = 0
        with transaction.atomic():
            for research in researches:
                for group in groups:
                    new_group, fields_count = _add_group(research, group)
                    created_groups += 1
                    created_fields += fields_count
                    self.stdout.write(self.style.SUCCESS(f"{research.pk}: группа «{new_group.title}» (order={new_group.order}, полей={fields_count})"))

        self.stdout.write(self.style.SUCCESS(f"Групп добавлено: {created_groups}, полей: {created_fields}"))
