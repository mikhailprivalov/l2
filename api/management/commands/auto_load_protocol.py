from django.core.management.base import BaseCommand
from api.parse_file.views import auto_create_protocol
from directory.models import Researches
from users.models import DoctorProfile


class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        :param
        path Путь до файла
        id_research 832
        id_doc_profile 3173
        titles fio-lastname-firstname-patronymic-sex-birthday-address-snils-enp-Диагноз-Дата_осмотра-Группа_здоровья-Вид_места_жительства
        """
        parser.add_argument("path", type=str)
        parser.add_argument("id_research", type=str)
        parser.add_argument("id_doc_profile", type=str)
        parser.add_argument("titles", type=str)

    def handle(self, *args, **kwargs):
        file_data = kwargs["path"]
        self.stdout.write("Path: " + file_data)
        id_doc_profile = int(kwargs["id_doc_profile"])
        id_research = int(kwargs["id_research"])
        doc_profile = DoctorProfile.objects.filter(pk=id_doc_profile).first()
        research = Researches.objects.filter(pk=id_research).first()
        title_fields = kwargs["titles"]
        financing_source_title = "омс"
        title_fields = title_fields.replace("-", ",").replace("_", " ")

        incorrect_patients = auto_create_protocol(title_fields, file_data, financing_source_title, research, doc_profile)
        print(incorrect_patients)  # noqa: T001
