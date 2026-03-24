from django.db import models
from django.db.models import Q
from clients.models import Card
from directions.models import Napravleniya
from directory.models import Researches
from podrazdeleniya.models import Podrazdeleniya
from users.models import DoctorProfile


class Drugs(models.Model):
    mnn = models.CharField(max_length=255, default="", null=True, blank=True, help_text='МНН препарата')
    trade_name = models.CharField(max_length=255, default="", null=True, blank=True, help_text='Торговое наименование препарата')

    def __str__(self):
        if self.trade_name and self.mnn:
            return f"{self.mnn} ({self.trade_name})"
        if self.mnn:
            return self.mnn
        return self.trade_name

    class Meta:
        verbose_name = 'МНН'
        verbose_name_plural = 'МНН'


class FormRelease(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Форма выпуска')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Форма выпуска'
        verbose_name_plural = 'Формы выпуска'


class MethodsReception(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Способ применения')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Способ приема'
        verbose_name_plural = 'Способы приема'


class DrugsTemplate(models.Model):
    title = models.CharField(max_length=100, help_text='Наименование шаблона')
    doc_create = models.ForeignKey(DoctorProfile, null=True, blank=True, help_text='Создатель шаблона', related_name='dt_doc_create', on_delete=models.CASCADE)
    time_create = models.DateTimeField(auto_now_add=True, help_text='Дата создания')
    who_update = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, help_text='Кто изменил шаблон', related_name='dt_who_update', on_delete=models.SET_NULL)
    time_update = models.DateTimeField(auto_now=True, help_text='Дата изменения шаблона')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Шаблон лекарственных препаратов'
        verbose_name_plural = 'Шаблоны лекарственных препаратов'

    @staticmethod
    def get_templates(doctor_profile):
        templates = [{
            "id": template.pk,
            "label": f"{template.title} ({template.doc_create.fio.strip()})",
        } for template in DrugsTemplate.objects.filter(Q(dtd_template__department=doctor_profile.podrazdeleniye) | Q(doc_create=doctor_profile))]
        return templates

    @staticmethod
    def is_template_exists(title):
        return DrugsTemplate.objects.filter(title=title).first()

    @staticmethod
    def template_permission(template_pk, doctor_profile):
        return DrugsTemplate.objects.filter(pk=template_pk, doc_create=doctor_profile).first()


class DrugsTemplatesDepartment(models.Model):
    template = models.ForeignKey(DrugsTemplate, help_text='Шаблон', related_name='dtd_template', on_delete=models.CASCADE)
    department = models.ForeignKey(Podrazdeleniya, help_text='Подразделение', related_name='dtd_department', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.template} | {self.department}'

    class Meta:
        verbose_name = 'Подразделение с доступом к шаблону лекарств'
        verbose_name_plural = 'Подразделения с доступом к шаблону лекарств'


class DrugsTemplatesRow(models.Model):
    template = models.ForeignKey(DrugsTemplate, related_name='dt_number', help_text='Шаблон', on_delete=models.CASCADE)
    drug = models.ForeignKey(Drugs, help_text="Препарат", related_name='drug_number', on_delete=models.CASCADE, db_index=True)
    form_release = models.ForeignKey(FormRelease, help_text="Форма выпуска", related_name='form_release_number', on_delete=models.CASCADE)
    method = models.ForeignKey(MethodsReception, help_text="Способ применения", related_name='method_number', on_delete=models.CASCADE)
    dosage = models.FloatField(help_text='Дозировка')
    units = models.CharField(max_length=8, help_text='Единицы измерения')
    days_count = models.PositiveSmallIntegerField(default=1, help_text='Количество дней приема лекарственного препарата')
    step = models.PositiveSmallIntegerField(default=1, blank=True, help_text='Шаг (для генерации)')
    comment = models.CharField(max_length=70, help_text='Комментарий', default='', blank=True)

    def __str__(self):
        return f'{self.template} | {self.drug}'

    class Meta:
        verbose_name = 'Строка шаблона лекарств'
        verbose_name_plural = 'Строки шаблона лекарств'


class DrugsTemplatesRowsTime(models.Model):
    row = models.ForeignKey(DrugsTemplatesRow, related_name='dtr_number', help_text='Строка шаблона', on_delete=models.CASCADE)
    times_medication = models.CharField(max_length=25, help_text='Время приема')

    def __str__(self):
        return f'{self.row} | {self.times_medication}'

    class Meta:
        verbose_name = 'Время приема лекарства в шаблоне'
        verbose_name_plural = 'Время приема лекарства в шаблоне'


class ProcedureList(models.Model):
    history = models.ForeignKey(Napravleniya, related_name='history_number', help_text='Номер истории', db_index=True, on_delete=models.CASCADE)
    diary = models.ForeignKey(Napravleniya, related_name='diaries_number', help_text='Номер дневника', db_index=True, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, db_index=True, help_text='Пациент', on_delete=models.CASCADE)
    drug = models.ForeignKey(Drugs, help_text="Препарат", on_delete=models.CASCADE, db_index=True)
    form_release = models.ForeignKey(FormRelease, help_text="Форма выпуска", on_delete=models.CASCADE)
    method = models.ForeignKey(MethodsReception, help_text="Способ применения", on_delete=models.CASCADE)
    dosage = models.FloatField(help_text='Дозировка')
    units = models.CharField(max_length=8, help_text='Единицы измерения')
    date_start = models.DateField(help_text="Дата начала")
    step = models.PositiveSmallIntegerField(default=1, blank=True, help_text='Шаг (для генерации)')
    date_end = models.DateField(help_text="Дата окончания включительно")
    doc_create = models.ForeignKey(DoctorProfile, related_name="doc_create_prescription", help_text='Создатель назначения', on_delete=models.CASCADE)
    time_create = models.DateTimeField(auto_now_add=True, help_text='Дата создания')
    cancel = models.BooleanField(default=False, blank=True, help_text='Отмена времени приема')
    who_cancel = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="pl_who_cancel", help_text='Кто отменил', on_delete=models.SET_NULL)
    research = models.ForeignKey(Researches, null=True, blank=True, help_text='Вид исследования из справочника', db_index=True, on_delete=models.CASCADE)
    comment = models.CharField(max_length=70, help_text='Комментарий', default='', blank=True)

    class Meta:
        verbose_name = 'Назначение'
        verbose_name_plural = 'Назначения'


class ProcedureListTimes(models.Model):
    prescription = models.ForeignKey(ProcedureList, help_text='Назначение из процедурного листа', on_delete=models.CASCADE)
    times_medication = models.DateTimeField(help_text='Время приема', db_index=True)
    executor = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_executor_prescription", help_text='Исполнитель', on_delete=models.SET_NULL)
    cancel = models.BooleanField(default=False, blank=True, help_text='Отмена времени приема')
    who_cancel = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="who_cancel", help_text='Кто отменил', on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Время из процедурного листа'
        verbose_name_plural = 'Время из процедурного листа'
