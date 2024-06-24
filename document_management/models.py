from django.contrib.postgres.fields import ArrayField
from django.db import models

from hospitals.models import Hospitals
from podrazdeleniya.models import Podrazdeleniya
from users.models import DoctorProfile


class GroupDocuments(models.Model):
    title = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        verbose_name = 'Группа Документов'
        verbose_name_plural = 'Группы документов'

    def __str__(self):
        return f'{self.title}'

    @property
    def json(self):
        return {
            'id': self.id,
            'title': self.title,
        }


class TypeDocuments(models.Model):
    title = models.CharField(max_length=128, blank=True, null=True)
    group_document = models.ForeignKey(GroupDocuments, default=None, blank=True, null=True, help_text='Группа документов', on_delete=models.SET_NULL)
    code = models.CharField(max_length=55, blank=True, null=True)

    class Meta:
        verbose_name = 'Вид документа'
        verbose_name_plural = 'Виды документов'

    def __str__(self):
        return f'{self.title}'

    @property
    def json(self):
        return {
            'id': self.id,
            'title': self.title,
        }


class Nomenclature(models.Model):
    title = models.CharField(max_length=128, blank=True, null=True)
    type_document = models.ForeignKey(TypeDocuments, default=None, blank=True, null=True, db_index=True, help_text='Тип документа', on_delete=models.SET_NULL)
    department = models.ForeignKey(Podrazdeleniya, related_name="department_nomenclature", help_text="Подразделение", db_index=True, null=True, blank=True, default=None, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Номенклатура'
        verbose_name_plural = 'Носенклатуры'

    def __str__(self):
        return f'{self.title}'


class Generators(models.Model):
    title = models.CharField(max_length=400, help_text="Название генератора номера")
    hospital = models.ForeignKey(Hospitals, on_delete=models.CASCADE, db_index=True, verbose_name='Больница')
    year = models.IntegerField(verbose_name='Год', db_index=True)
    is_active = models.BooleanField(verbose_name='Активность диапазона', db_index=True)
    start = models.PositiveBigIntegerField(verbose_name='Начало диапазона')
    end = models.PositiveBigIntegerField(verbose_name='Конец диапазона', null=True, blank=True, default=None)
    last = models.PositiveBigIntegerField(verbose_name='Последнее значение диапазона', null=True, blank=True)
    free_numbers = ArrayField(models.PositiveBigIntegerField(verbose_name='Свободные номера'), default=list, blank=True)
    prepend_length = models.PositiveSmallIntegerField(verbose_name='Длина номера', help_text='Если номер короче, впереди будет добавлено недостающее кол-во "0"')
    department = models.ForeignKey(
    Podrazdeleniya, related_name="department_for_generator", help_text="Подразделение", db_index=True, null=True, blank=True, default=None, on_delete=models.SET_NULL
)

    def __str__(self):
        return f"{self.hospital} {self.year} {self.is_active} {self.start} — {self.end} ({self.last})"

    class Meta:
        verbose_name = 'Генератор номеров'
        verbose_name_plural = 'Генераторы номеров'


class TypeDocumentsFields(models.Model):
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
    type_document = models.ForeignKey(TypeDocuments, default=None,  db_index=True, blank=True, null=True, help_text='Тип документа', on_delete=models.SET_NULL)
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
        verbose_name = 'Реквизит для документа'
        verbose_name_plural = 'Реквизит для документов'

    def __str__(self):
        return f'{self.type_document}'


class Documents(models.Model):
    type_document = models.ForeignKey(TypeDocuments,  db_index=True, default=None, blank=True, null=True, help_text='Тип документа', on_delete=models.SET_NULL)
    who_create = models.ForeignKey(DoctorProfile, db_index=True, default=None, blank=True, null=True, help_text='Создатель документа', on_delete=models.SET_NULL)
    create_at = models.DateTimeField(auto_now_add=True, help_text='Дата создания документа', db_index=True)

    class Meta:
        verbose_name = 'Документ экземпляр'
        verbose_name_plural = 'Документы экземляров'

    def __str__(self):
        return f'{self.type_document}'


class AttributesDocumentResult(models.Model):
    document = models.ForeignKey(Documents, default=None, blank=True, null=True, help_text='Тип документа', on_delete=models.SET_NULL)
    create_at = models.DateTimeField(auto_now_add=True, help_text='Дата создания/изменения', db_index=True)
    who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, help_text='Создатель', on_delete=models.SET_NULL)
    value = models.TextField(null=True, blank=True, help_text='Значение')
    attribute = models.ForeignKey(TypeDocumentsFields, default=None, blank=True, null=True, related_name="who_create", help_text='Создатель документа', on_delete=models.SET_NULL)
    attribute_type = models.SmallIntegerField(default=None, blank=True, choices=TypeDocumentsFields.TYPES, null=True)

    class Meta:
        verbose_name = 'Реквизит для документа'
        verbose_name_plural = 'Реквизит для документов'

    def __str__(self):
        return f'{self.document}'
