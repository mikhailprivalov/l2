import hashlib

from django.db import models

from appconf.manager import SettingManager
from directions.models import Napravleniya


class ResultFeed(models.Model):
    CATEGORY_LABORATORY = 'laboratory'
    CATEGORY_CONSULTATIONS = 'consultations'
    CATEGORY_DIAGNOSTICS = 'diagnostics'
    CATEGORIES = (
        (CATEGORY_LABORATORY, 'Лаборатория'),
        (CATEGORY_CONSULTATIONS, 'Консультации'),
        (CATEGORY_DIAGNOSTICS, 'Диагностика'),
    )

    unique_id = models.CharField(max_length=128, db_index=True, unique=True)
    hospital = models.ForeignKey('hospitals.Hospitals', on_delete=models.CASCADE, db_index=True)
    individual = models.ForeignKey('clients.Individual', on_delete=models.CASCADE, db_index=True)
    card = models.ForeignKey('clients.Card', on_delete=models.CASCADE)
    direction = models.ForeignKey('directions.Napravleniya', on_delete=models.CASCADE, db_index=True)
    service_names = models.TextField()
    department_name = models.CharField(max_length=128, blank=True, null=True)
    category = models.CharField(max_length=128, choices=CATEGORIES, db_index=True)
    direction_created_at = models.DateTimeField()
    result_confirmed_at = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name = 'Запись в ленте результатов'
        verbose_name_plural = 'Записи в ленте результатов'
        ordering = ('-result_confirmed_at',)

    def __str__(self):
        return f'{self.direction} {self.get_category_display()} {self.result_confirmed_at:%Y-%m-%d %H:%M:%S}'

    @staticmethod
    def insert_feed_by_direction(direction: Napravleniya):
        if not SettingManager.l2('feed'):
            return None

        if not direction.is_all_confirm():
            return None

        category = None
        department_name_parts = []

        service_names_list = []
        for iss in direction.issledovaniya_set.all().order_by('research__sort_weight'):
            research = iss.research
            if not research:
                continue
            service_names_list.append(research.get_title())
            is_desc = research.desc
            is_doc_referral = research.is_doc_referral
            if not is_desc:
                category = ResultFeed.CATEGORY_LABORATORY
            elif is_doc_referral:
                category = ResultFeed.CATEGORY_CONSULTATIONS
            elif iss.research.is_paraclinic:
                category = ResultFeed.CATEGORY_DIAGNOSTICS

            department_name = research.get_podrazdeleniye_short_title()

            if department_name and department_name not in department_name_parts:
                department_name_parts.append(department_name)

        if not category:
            return None

        direction.sync_confirmed_fields(skip_post=True)
        hospital = direction.get_hospital()
        individual = direction.client.individual
        card = direction.client
        direction_created_at = direction.data_sozdaniya
        result_confirmed_at = direction.last_confirmed_at
        service_names = '\n'.join(service_names_list)
        department_name_parts.sort()
        department_name = ', '.join(department_name_parts) if department_name_parts else None

        unique_id_raw = f'{individual.pk}_{card.pk}_{direction.pk}'
        unique_id = hashlib.sha1(unique_id_raw.encode('utf-8')).hexdigest()

        return ResultFeed.objects.create(
            unique_id=unique_id,
            hospital=hospital,
            individual=individual,
            card=card,
            direction=direction,
            service_names=service_names,
            department_name=department_name,
            category=category,
            direction_created_at=direction_created_at,
            result_confirmed_at=result_confirmed_at,
        )

    @staticmethod
    def remove_feed_by_direction(direction: Napravleniya):
        ResultFeed.objects.filter(direction=direction).delete()
