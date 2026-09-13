from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from directory.models import ParaclinicInputField, ParaclinicInputGroups, ParaclinicTemplateName, Researches
from podrazdeleniya.models import Podrazdeleniya

QUOTES = '"\'«»“”„‘’`´'


def strip_quotes(value) -> str:
    text = str(value or "")
    for ch in QUOTES:
        text = text.replace(ch, "")
    return text.strip()


def normalize_title(value) -> str:
    return strip_quotes(value).replace("/", "|").replace("\\", "|").strip()


class Command(BaseCommand):
    help = "Create paraclinic researches from semicolon-separated titles, copying protocol from a template research"

    def add_arguments(self, parser):
        parser.add_argument("titles", type=str)
        parser.add_argument("department_id", type=str)
        parser.add_argument("template_research_id", type=str)

    def handle(self, *args, **kwargs):
        titles = [normalize_title(t) for t in strip_quotes(kwargs["titles"]).split(";") if normalize_title(t)]
        if not titles:
            raise CommandError("No titles provided")

        try:
            department_id = int(strip_quotes(kwargs["department_id"]))
        except ValueError:
            raise CommandError(f"Invalid department id: {kwargs['department_id']}")
        department = Podrazdeleniya.objects.filter(pk=department_id).first()
        if not department:
            raise CommandError(f"Department {department_id} not found")
        if department.p_type != Podrazdeleniya.PARACLINIC:
            raise CommandError(f"Department {department_id} is not paraclinic (p_type={department.p_type})")

        try:
            template_research_id = int(strip_quotes(kwargs["template_research_id"]))
        except ValueError:
            raise CommandError(f"Invalid template research id: {kwargs['template_research_id']}")
        template = Researches.objects.filter(pk=template_research_id).first()
        if not template:
            raise CommandError(f"Template research {template_research_id} not found")

        template_groups = list(ParaclinicInputGroups.objects.filter(research=template).order_by("order"))
        template_fields_by_group = {group.pk: list(ParaclinicInputField.objects.filter(group=group).order_by("order")) for group in template_groups}

        created = 0
        skipped = 0
        for title in titles:
            if Researches.objects.filter(title=title, podrazdeleniye=department).exists():
                self.stdout.write(self.style.WARNING(f"Skip existing: {title}"))
                skipped += 1
                continue
            research = self._create_research(title, department, template, template_groups, template_fields_by_group)
            self.stdout.write(self.style.SUCCESS(f"Created {research.pk}: {research.title}"))
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created}, skipped {skipped}"))

    def _create_research(self, title, department, template, template_groups, template_fields_by_group):
        with transaction.atomic():
            research = Researches(
                title=title,
                podrazdeleniye=department,
                is_paraclinic=True,
                direction_form=template.direction_form,
                result_form=template.result_form,
                has_own_form_result=template.result_form > 0,
            )
            research.save()
            if research.ensure_internal_code():
                research.save(update_fields=["internal_code"])

            for group in template_groups:
                new_group = ParaclinicInputGroups(
                    title=group.title,
                    show_title=group.show_title,
                    research=research,
                    order=group.order,
                    hide=group.hide,
                    visibility=group.visibility,
                    fields_inline=group.fields_inline,
                    cda_option_id=group.cda_option_id,
                )
                new_group.save()
                for field in template_fields_by_group[group.pk]:
                    ParaclinicInputField(
                        title=field.title,
                        group=new_group,
                        order=field.order,
                        hide=field.hide,
                        field_type=field.field_type,
                        cda_option_id=field.cda_option_id,
                        input_templates=field.input_templates or "[]",
                        lines=field.lines,
                        default_value=field.default_value or "",
                    ).save()

            ParaclinicTemplateName.make_default(research)
            return research
