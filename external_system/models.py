from django.db import models

from directions.models import Napravleniya
from hospitals.models import Hospitals
from podrazdeleniya.models import Podrazdeleniya


class FsliRefbookTest(models.Model):
    """
    Таблица справочников ФСЛИ: https://nsi.rosminzdrav.ru/#!/refbook/1.2.643.5.1.13.13.11.1080
    """

    code_fsli = models.CharField(max_length=20, db_index=True, help_text='Уникальный код ФСЛИ')
    code_loinc = models.CharField(max_length=20, help_text='Код LOINC')
    title = models.CharField(max_length=1000, db_index=True, help_text='Полное наименование')
    english_title = models.CharField(max_length=1000, db_index=True, help_text='Английское наименование')
    short_title = models.CharField(max_length=1000, db_index=True, help_text='Краткое наименование')
    synonym = models.CharField(max_length=255, help_text='Синоним')
    analit = models.CharField(max_length=255, help_text='Аналит')
    analit_props = models.CharField(max_length=255, help_text='Свойства аналита')
    dimension = models.CharField(max_length=255, help_text='Размерность')
    unit = models.CharField(max_length=100, help_text='Единица измерения')
    sample = models.CharField(max_length=100, help_text='Образец')
    time_characteristic_sample = models.CharField(max_length=100, help_text='Временная характеристика образца')
    method_type = models.CharField(max_length=500, help_text='Тип метода')
    scale_type = models.CharField(max_length=100, help_text='Тип шкалы измерения')
    actual = models.CharField(max_length=100, help_text='Статус')
    active = models.BooleanField(default=True, help_text='Единица измерения')
    test_group = models.CharField(max_length=100, help_text='Группа тестов')
    code_nmu = models.CharField(max_length=100, help_text='Код НМУ')
    ordering = models.IntegerField(help_text='Порядок сортировки', blank=True, default=None, null=True)

    def __str__(self):
        return f"{self.code_fsli} – {self.title}"


class InstrumentalResearchRefbook(models.Model):
    """
    Таблица справочников: https://nsi.rosminzdrav.ru/#!/refbook/1.2.643.5.1.13.13.11.1471/
    """

    code_nsi = models.CharField(default='', max_length=20, db_index=True, help_text='Уникальный код')
    title = models.CharField(default='', max_length=1000, db_index=True, help_text='Полное наименование')
    method = models.CharField(default='', max_length=300, db_index=True, help_text='Метод')
    area = models.CharField(default='', max_length=300, db_index=True, help_text='Область')
    localization = models.CharField(default='', max_length=300, db_index=True, help_text='Локализация')
    code_nmu = models.CharField(default='', max_length=300, db_index=True, help_text='Код исследования НМУ')

    def __str__(self):
        return f"{self.code_nsi} – {self.title}-{self.area}-{self.code_nmu}"


class BodySiteRefbook(models.Model):
    """
    Область исследования: 1.2.643.2.69.1.1.1.57/
    """

    code = models.CharField(max_length=20, db_index=True, help_text='Код')
    title = models.CharField(max_length=1000, db_index=True, help_text='Полное наименование')

    def __str__(self):
        return f"{self.code} – {self.title}"


class ArchiveMedicalDocuments(models.Model):
    local_uid = models.UUIDField(null=True, default=None, blank=True, help_text='uid_localid', db_index=True)
    direction = models.ForeignKey(Napravleniya, null=True, help_text='Направление', db_index=True, on_delete=models.SET_NULL)
    status = models.SmallIntegerField(default=-1, help_text='Статус')
    message_id = models.UUIDField(null=True, default=None, blank=True, unique=True, help_text='message_id_uuid', db_index=True)
    time_exec = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время запроса на регистрацию')
    organization = models.ForeignKey(Hospitals, null=True, blank=True, default=None, help_text="Больница", db_index=True, on_delete=models.SET_NULL)
    department = models.ForeignKey(Podrazdeleniya, help_text="Подразделение", null=True, blank=True, default=None, db_index=True, on_delete=models.SET_NULL)
    kind = models.SmallIntegerField(default=-1, blank=True, help_text='oid документа', db_index=True)
    emdr_id = models.CharField(max_length=128, blank=True, default='', help_text="Номер ЭМД в реестре")
    registration_date = models.DateTimeField(null=True, blank=True, help_text='Дата создания записи в реестр')
    message = models.TextField(default="", null=True, blank=True, help_text='Сообщение')

    def __str__(self):
        return f"{self.direction.pk} – {self.time_exec}"


class TypesMedicalDocuments(models.Model):
    oid = models.SmallIntegerField(default=-1, blank=True, help_text='oid документа', db_index=True)
    name = models.CharField(max_length=255, help_text='Наименование')

    def __str__(self):
        return f"{self.oid} - {self.name}"


class CdaFields(models.Model):
    code = models.IntegerField(default=-1, blank=True, help_text='code документа', db_index=True)
    title = models.CharField(max_length=255, default="", help_text='Наименование', db_index=True)
    is_doc_refferal = models.BooleanField(default=False, blank=True, help_text="Это исследование-направление к врачу", db_index=True)
    is_treatment = models.BooleanField(default=False, blank=True, help_text="Это лечение", db_index=True)
    is_form = models.BooleanField(default=False, blank=True, help_text="Это формы, cправки, направления", db_index=True)
    is_extract = models.BooleanField(default=False, blank=True, help_text="Это выписка", db_index=True)

    def __str__(self):
        return f"{self.code} - {self.title}"

    @staticmethod
    def get_cda_params(is_doc_refferal, is_treatment, is_form, is_extract):
        result = [{"id": -1, "label": "Пусто"}]
        if is_doc_refferal:
            result = [{"id": -1, "label": "Пусто"}, *[{"id": x.pk, "label": f"{x.title} - {x.code}"} for x in CdaFields.objects.filter(is_doc_refferal=True).order_by("title")]]
        elif is_treatment:
            result = [{"id": -1, "label": "Пусто"}, *[{"id": x.pk, "label": f"{x.title} - {x.code}"} for x in CdaFields.objects.filter(is_treatment=True).order_by("title")]]
        elif is_form:
            result = [{"id": -1, "label": "Пусто"}, *[{"id": x.pk, "label": f"{x.title} - {x.code}"} for x in CdaFields.objects.filter(is_form=True).order_by("title")]]
        elif is_extract:
            result = [{"id": -1, "label": "Пусто"}, *[{"id": x.pk, "label": f"{x.title} - {x.code}"} for x in CdaFields.objects.filter(is_extract=True).order_by("title")]]

        return result


class ProfessionsWorkersPositionsRefbook(models.Model):
    """
    Профессии рабочих и должностей служащих: 1.2.643.5.1.13.13.99.2.855
    """

    code = models.CharField(max_length=20, db_index=True, help_text='Код')
    title = models.CharField(max_length=1000, db_index=True, help_text='Полное наименование')

    def __str__(self):
        return f"{self.code} – {self.title}"

    class Meta:
        verbose_name = "Профессия рабочих и должностей служащих"
        verbose_name_plural = "Профессии рабочих и должностей служащих"
