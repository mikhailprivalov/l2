from django.core.management.base import BaseCommand

from directory.models import ParaclinicInputField


class Command(BaseCommand):
    help = "Найти поля протокола по точному названию и вывести их id"

    def add_arguments(self, parser):
        parser.add_argument("--title", required=True, help='Точное название поля, например "Файл"')

    def handle(self, *args, **options):
        title = options["title"]
        fields = ParaclinicInputField.objects.filter(title=title).select_related("group", "group__research").order_by("pk")
        ids = []
        for field in fields:
            ids.append(str(field.pk))
            research_title = field.group.research.title if field.group_id and field.group.research_id else ""
            group_title = field.group.title if field.group_id else ""
            self.stdout.write(f"{field.pk}\t{research_title}\t{group_title}")
        self.stdout.write(",".join(ids))
