import datetime

from django.core.management.base import BaseCommand

from clients.models import Individual, Document, DocumentType
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        current_date = datetime.datetime.now()
        start_date = datetime.datetime(current_date.year - 14, current_date.month, current_date.day)
        self.stdout.write(f"Текущая дата: {current_date}")
        self.stdout.write(f"Начальная дата: {start_date}")
        passport_type = DocumentType.objects.filter(title__startswith="Паспорт гражданина РФ").first()
        if passport_type:
            children_individual = Individual.objects.filter(birthday__range=[start_date, current_date])
            for individual in children_individual:
                passport = Document.objects.filter(individual_id=individual.pk, document_type_id=passport_type.pk).first()
                if passport:
                    passport.delete()
                    self.stdout.write(f"Пациент: {individual.fio()} - паспорт удалён")
        else:
            self.stdout.write("'Паспорт гражданина РФ', нет такого документа")
