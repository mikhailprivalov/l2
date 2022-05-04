from django.db import models
from users.models import DoctorProfile


class Departments(models.Model):
    title = models.CharField(max_length=255, help_text='структурное подразделение')

    class Meta:
        verbose_name = 'Структурное подразделение'
        verbose_name_plural = 'структурные подразделения'


class Persons(models.Model):
    last_name = models.CharField(max_length=255, help_text='Фамилия')
    first_name = models.CharField(max_length=255, help_text='Имя')
    patronymic = models.CharField(max_length=255, help_text='Отчество')
    snils = models.CharField(max_length=255, help_text='СНИЛС')

    class Meta:
        verbose_name = 'Физлицо'
        verbose_name_plural = 'Физлица'


class TypeWorkTime(models.Model):
    title = models.CharField(max_length=255, help_text='Занятость (осн | внутр.свом| внеш. совм)')

    class Meta:
        verbose_name = 'Тип занятости'
        verbose_name_plural = 'Типы занятости'


class Posts(models.Model):
    title = models.CharField(max_length=255, help_text='Справочник должностей')

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'


class Employees(models.Model):
    person = models.ForeignKey(Persons, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    post = models.ForeignKey(Posts, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    type_post = models.ForeignKey(TypeWorkTime, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    department = models.ForeignKey(Departments, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    number_unit_time = models.DecimalField(max_digits=10, decimal_places=2, default=1, help_text='Кол-во единиц ставок')
    tabel_number = models.CharField(max_length=255, help_text='Табельный номер', db_index=True)

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'


class TabelDocuments(models.Model):
    STATUS_APPROVED = 'STATUS_APPROVED'
    STATUS_CHECK = 'STATUS_CHECK'
    STATUS_TO_CORRECT = 'STATUS_TO_CORRECT'

    STATUS_TYPES = (
        (STATUS_APPROVED, 'Утвержден'),
        (STATUS_CHECK, 'На проверке'),
        (STATUS_TO_CORRECT, 'Исправить'),
    )

    doc_confirmation = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True, help_text='Профиль автора', on_delete=models.SET_NULL)
    doc_confirmation_string = models.CharField(max_length=64, null=True, blank=True, default=None)
    time_confirmation = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время подтверждения результата')
    month_tabel = models.DateField(help_text='Месяц учета', db_index=True, default=None, blank=True, null=True)
    department = models.ForeignKey(Departments, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    is_actual = models.BooleanField(help_text="Акутальный", default=True)
    version = models.PositiveSmallIntegerField(default=None, db_index=True, blank=True, null=True)
    parent_document = models.ForeignKey('self', related_name='parent_tabel_document', help_text="Документ основание", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    comment_checking = models.TextField(blank=True, null=True, help_text="Комментарий от проверяющего")
    status = models.CharField(max_length=20, null=True, blank=True, default=None, db_index=True, choices=STATUS_TYPES, help_text="Статус")
    doc_change_status = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True, help_text='Профиль проверяющего', on_delete=models.SET_NULL)
    doc_change_status_string = models.CharField(max_length=64, null=True, blank=True, default=None)
    time_change_status = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время изменения статуса')

    class Meta:
        verbose_name = 'Табель'
        verbose_name_plural = 'Табели'


class FactTimeWork(models.Model):
    STATUS_WORK = 'STATUS_WORK'
    STATUS_HOLIDAY = 'STATUS_HOLIDAY'
    STATUS_SICK = 'STATUS_HOLIDAY'
    STATUS_BUSINESS_TRIP = 'STATUS_BUSINESS_TRIP'
    STATUS_DISMISS = 'STATUS_DISMISS'

    STATUS_TYPES = (
        (STATUS_WORK, 'Работа'),
        (STATUS_HOLIDAY, 'Отпуск'),
        (STATUS_HOLIDAY, 'Больничный'),
        (STATUS_BUSINESS_TRIP, 'Командировка'),
        (STATUS_DISMISS, 'Уволен'),
    )

    employee = models.ForeignKey(Employees, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    tabel_document = models.ForeignKey(TabelDocuments, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    date = models.DateField(help_text='Дата учета', db_index=True, default=None, blank=True, null=True)
    night_hours = models.DecimalField(max_digits=10, decimal_places=2)
    common_hours = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, null=True, blank=True, default=None, db_index=True, choices=STATUS_TYPES, help_text="Статус")

    class Meta:
        verbose_name = 'Табель времени'
        verbose_name_plural = 'Табели времени'


class DocumentFactTimeWork(models.Model):
    tabel_document = models.ForeignKey(TabelDocuments, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    data_document = models.TextField(blank=True, null=True, help_text="Данные документа")

    class Meta:
        verbose_name = 'Табель документ'
        verbose_name_plural = 'Табель документы'


class Holidays(models.Model):
    year = models.IntegerField
    day = models.DateField()

    class Meta:
        verbose_name = 'Праздничный день'
        verbose_name_plural = 'Праздничные дни'
