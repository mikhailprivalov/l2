from django.db import models


class TypeInstitutionEducation(models.Model):
    title = models.CharField(max_length=64, verbose_name='Вид учреждения - Школа, Коледж, Техникум, Институт')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Тип учреждения'
        verbose_name_plural = 'Типы учреждения'


class InstitutionTitle(models.Model):
    title = models.CharField(max_length=64, verbose_name='Название учреждения')
    type = models.ForeignKey(TypeInstitutionEducation, default=None, on_delete=models.CASCADE, verbose_name='Тип учреждение')
    address = models.CharField(max_length=128, blank=True, default='', help_text="Адрес")
    address_fias = models.CharField(max_length=128, blank=True, default=None, null=True, help_text="ФИАС Адрес")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Образовательное учреждение'
        verbose_name_plural = 'Образовательные учреждение'


class LevelEducation(models.Model):
    title = models.CharField(max_length=64, verbose_name='Уровень образования - среднее, высшее')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Уровень образования'
        verbose_name_plural = 'Уровни образования'


class DocumentTypeEducation(models.Model):
    title = models.CharField(max_length=64, verbose_name='Вид документа образования - аттестат, диплом, сертификат')
    level_education = models.ForeignKey(LevelEducation, help_text="Уровень образования", db_index=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.title


class DocumentEducation(models.Model):
    document_type = models.ForeignKey(DocumentTypeEducation, help_text="Вид документа", db_index=True, null=True, on_delete=models.SET_NULL)
    serial = models.CharField(max_length=30, blank=True, null=True,  help_text="Серия")
    number = models.CharField(max_length=30, blank=True, null=True, help_text="Номер")
    date_issued = models.DateField(help_text="Дата документа", blank=True, null=True)
    registration_number = models.CharField(max_length=30, blank=True, help_text="Регистрационный номер")
    is_original_received = models.BooleanField(default=False, blank=True, help_text="Оригинал документа")
    source_original_received = models.CharField(max_length=30, blank=True, help_text="Исчтоник оригинального документа")
    date_received_original = models.DateField(help_text="Дата получения документа", blank=True, null=True)
    card = models.ForeignKey('clients.Card', db_index=True, on_delete=models.CASCADE)


class FormEducation(models.Model):
    title = models.CharField(max_length=100, verbose_name='Наименование', help_text='Очная, заочная, очно-заочная')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Форма обучения'
        verbose_name_plural = 'Формы обучения'


STATEMENTS_STAGE = (
        ('main', 'Основной'),
        ('additional', 'Дополнительный'),
    )

STATEMENTS_STATUS = (
        ('accepted', 'Принято'),
        ('checked', 'Проверено'),
        ('rejected', 'Отклонено'),
    )


class StatementsSource(models.Model):
    title = models.CharField(max_length=100, verbose_name='Наименование', help_text='ЕГПУ, ЛК и т.д')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Источник заявления'
        verbose_name_plural = 'Источники заявлений'


class Statements(models.Model):
    card = models.ForeignKey('clients.Card', db_index=True, on_delete=models.CASCADE)
    speciality = models.ForeignKey('users.Speciality', verbose_name='Специальность-направление', help_text='Лечебное дело, Стоматология и т.д', db_index=True, on_delete=models.CASCADE)
    form = models.ForeignKey(FormEducation, verbose_name='Форма обучения', db_index=True, on_delete=models.CASCADE)
    source = models.ForeignKey(StatementsSource, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=STATEMENTS_STATUS, blank=True, null=True, default=STATEMENTS_STATUS[0][0], verbose_name='Статус заявления')
    stage = models.CharField(max_length=15, choices=STATEMENTS_STAGE, blank=True, null=True, default=STATEMENTS_STAGE[0][0], verbose_name='Этап заявления')

    def __str__(self):
        return f"{self.card} - {self.speciality} - {self.form}"

    class Meta:
        verbose_name = 'Заявление'
        verbose_name_plural = 'Заявления'


class ExamType(models.Model):
    title = models.CharField(max_length=255, verbose_name='Наименование', help_text='ЕГЭ, ВИ, ВИ СПО и т.д')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Тип экзамена'
        verbose_name_plural = 'Типы экзаменов'


EXAM_STATYS = (
        ('not_checked', 'Не проверен'),
        ('checked', 'Проверен'),
    )


class Subjects(models.Model):
    title = models.CharField(max_length=255, verbose_name='Наименование', help_text='Химия/основы химии, Математика и т.д')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'


class EntranceExam(models.Model):
    card = models.ForeignKey('clients.Card', db_index=True, on_delete=models.CASCADE)
    type = models.ForeignKey(ExamType, verbose_name='Тип испытания', db_index=True, on_delete=models.CASCADE)
    subjects = models.ForeignKey(Subjects, verbose_name='Предмет', db_index=True, on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Балл')
    document_number = models.CharField(max_length=255, blank=True, null=True, verbose_name='Номер документа')
    document_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата документа')
    status = models.CharField(max_length=15, choices=EXAM_STATYS, blank=True, null=True, default=EXAM_STATYS[0][0], verbose_name='Статус испытания')

    def __str__(self):
        return f"{self.card} - {self.type} - {self.subjects} - {self.score}"

    class Meta:
        verbose_name = 'Вступительное испытание'
        verbose_name_plural = 'Вступительные испытания'


class AchievementType(models.Model):
    title = models.CharField(max_length=255, verbose_name='Наименование', help_text='ГТО, Олимпиада')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Тип достижения'
        verbose_name_plural = 'Типы достижений'


ACHIEVEMENT_STATUS = (
        ('declared', 'Заявлено'),
        ('checked ', 'Проверено'),
        ('rejected', 'Отклонено'),
    )


class Achievement(models.Model):
    card = models.ForeignKey('clients.Card', db_index=True, on_delete=models.CASCADE)
    type = models.ForeignKey(AchievementType, verbose_name='Тип достижения', db_index=True, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=ACHIEVEMENT_STATUS, blank=True, null=True, default=ACHIEVEMENT_STATUS[0][0], verbose_name='Статус достижения')
    document_number = models.CharField(max_length=255, blank=True, null=True, verbose_name='Номер документа')
    document_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата документа')

    def __str__(self):
        return f"{self.card} - {self.type.title}"

    class Meta:
        verbose_name = 'Достижение'
        verbose_name_plural = 'Достижения'


class SpecialRightsType(models.Model):
    title = models.CharField(max_length=255, verbose_name='Наименование', help_text='Инвалид, сирота, военнослужащий')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Тип особых прав'
        verbose_name_plural = 'Типы особых прав'


class SpecialRights(models.Model):
    title = models.CharField(max_length=255, verbose_name='Наименование', help_text='Инвалид 1ой группы')
    type = models.ForeignKey(SpecialRightsType, blank=True, null=True, verbose_name='Тип прав', db_index=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Особые права справочник'
        verbose_name_plural = 'Особые права справочник'


class CardSpecialRights(models.Model):
    card = models.ForeignKey('clients.Card', db_index=True, on_delete=models.CASCADE)
    right = models.ForeignKey(SpecialRights, db_index=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.card} - {self.right.title}"

    class Meta:
        verbose_name = 'Особые права'
        verbose_name_plural = 'Особые права'
