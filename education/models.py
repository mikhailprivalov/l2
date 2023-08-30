from django.db import models
from django.utils import timezone
import education.sql_func as sql_func


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

    @staticmethod
    def get_education_documents_tree():
        documents = DocumentTypeEducation.objects.all().prefetch_related('level_education')
        doc_dict = {}
        for i in documents:
            if doc_dict.get(i.level_education.title):
                doc_dict[i.level_education.title].append({"id": i.pk, "label": i.title})
            elif not doc_dict.get(i.level_education.title):
                doc_dict[i.level_education.title] = [{"id": i.pk, "label": i.title}]
        count = 0
        result_tree = []
        for key, value in doc_dict.items():
            result_tree.append({"id": f'а{+count}', "label": key, "children": value})
            count += 1
        return result_tree


class DocumentEducation(models.Model):
    document_type = models.ForeignKey(DocumentTypeEducation, help_text="Вид документа", db_index=True, null=True, on_delete=models.SET_NULL)
    serial = models.CharField(max_length=30, blank=True, null=True, help_text="Серия")
    number = models.CharField(max_length=30, blank=True, null=True, help_text="Номер")
    date_issued = models.DateField(help_text="Дата документа", blank=True, null=True)
    registration_number = models.CharField(max_length=30, blank=True, help_text="Регистрационный номер")
    is_original_received = models.BooleanField(default=False, blank=True, help_text="Оригинал документа")
    source_original_received = models.CharField(max_length=30, blank=True, help_text="Исчтоник оригинального документа")
    date_received_original = models.DateField(help_text="Дата получения документа", blank=True, null=True)
    card = models.ForeignKey('clients.Card', db_index=True, on_delete=models.CASCADE)


class FormEducation(models.Model):
    title = models.CharField(max_length=100, verbose_name='Наименование формы обучения', help_text='Очная, заочная, очно-заочная')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Форма обучения'
        verbose_name_plural = 'Формы обучения'


class ApplicationSourceEducation(models.Model):
    title = models.CharField(max_length=100, verbose_name='Наименование источника заявления', help_text='ЕГПУ, ЛК и т.д')

    def __str__(self):
        return self.title

    @staticmethod
    def get_application_source() -> list[dict]:
        sources = [{"id": source.pk, "label": source.title} for source in ApplicationSourceEducation.objects.all()]
        return sources

    class Meta:
        verbose_name = 'Источник заявления'
        verbose_name_plural = 'Источники заявлений'


class ApplicationEducation(models.Model):
    APPLICATION_STAGE = (
        ('main', 'Основной'),
        ('additional', 'Дополнительный'),
    )

    APPLICATION_STATUS = (
        ('accepted', 'Принято'),
        ('checked', 'Проверено'),
        ('rejected', 'Отклонено'),
    )

    card = models.ForeignKey('clients.Card', db_index=True, on_delete=models.CASCADE)
    speciality = models.ForeignKey('users.Speciality', verbose_name='Специальность-направление', help_text='Лечебное дело, Стоматология и т.д', db_index=True, on_delete=models.CASCADE)
    form = models.ForeignKey(FormEducation, verbose_name='Форма обучения', db_index=True, on_delete=models.CASCADE)
    application_source = models.ForeignKey(ApplicationSourceEducation, verbose_name='Источник заявления', on_delete=models.CASCADE)
    application_status = models.CharField(max_length=15, choices=APPLICATION_STATUS, blank=True, null=True, default=APPLICATION_STATUS[0][0], verbose_name='Статус заявления')
    application_stage = models.CharField(max_length=15, choices=APPLICATION_STAGE, blank=True, null=True, default=APPLICATION_STAGE[0][0], verbose_name='Этап заявления')
    date = models.DateTimeField(verbose_name='Дата подачи заявления', default=timezone.now)
    is_enrolled = models.BooleanField(default=False, verbose_name='Зачислен')
    is_expelled = models.BooleanField(default=False, verbose_name='Отчислен')

    def __str__(self):
        return f"{self.card} - {self.speciality} - {self.form}"

    @staticmethod
    def get_application_status() -> list[dict]:
        statuses = [{"id": i[0], "label": i[1]} for i in ApplicationEducation.APPLICATION_STATUS]
        return statuses

    @staticmethod
    def get_application_stage() -> list[dict]:
        stages = [{"id": i[0], "label": i[1]} for i in ApplicationEducation.APPLICATION_STAGE]
        return stages

    @staticmethod
    def get_applications_by_card(card_pk) -> list[dict]:
        applications = []
        data = sql_func.get_applications_by_card(card_pk)
        current_application = -1
        for i in data:
            if current_application != i.application_pk:
                applications.append({
                    "pk": i.application_pk,
                    "date": i.date.strftime('%d.%m.%Y'),
                    "speciality": i.spec_title,
                    "subjects": [{"title": i.subject_title, "score": i.score}]
                })
            else:
                applications[-1]["subjects"].append({"title": i.subject_title, "score": i.score})
            current_application = i.application_pk
        return applications

    class Meta:
        verbose_name = 'Заявление'
        verbose_name_plural = 'Заявления'


class ExamType(models.Model):
    title = models.CharField(max_length=255, verbose_name='Наименование типа экзамена', help_text='ЕГЭ, ВИ, ВИ СПО и т.д')

    def __str__(self):
        return self.title

    @staticmethod
    def get_types() -> list[dict]:
        types = [{"id": type.pk, "label": type.title} for type in ExamType.objects.all()]
        return types

    class Meta:
        verbose_name = 'Тип экзамена'
        verbose_name_plural = 'Типы экзаменов'


class Subjects(models.Model):
    title = models.CharField(max_length=255, verbose_name='Наименование предмета', help_text='Химия/основы химии, Математика и т.д')

    def __str__(self):
        return self.title

    @staticmethod
    def get_subjects() -> list[dict]:
        subjects = [{"id": subject.pk, "label": subject.title} for subject in Subjects.objects.all()]
        return subjects

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
    is_checked = models.BooleanField(default=False, verbose_name='Статус проверки экзамена')

    def __str__(self):
        return f"{self.card} - {self.type} - {self.subjects} - {self.score}"

    class Meta:
        verbose_name = 'Вступительное испытание'
        verbose_name_plural = 'Вступительные испытания'


class AchievementType(models.Model):
    title = models.CharField(max_length=255, verbose_name='Наименование типа достижения', help_text='ГТО, Олимпиада')

    def __str__(self):
        return self.title

    @staticmethod
    def get_types() -> list[dict]:
        types = [{"id": type.pk, "label": type.title} for type in AchievementType.objects.all()]
        return types

    class Meta:
        verbose_name = 'Тип достижения'
        verbose_name_plural = 'Типы достижений'


class Achievement(models.Model):
    ACHIEVEMENT_STATUS = (
        ('declared', 'Заявлено'),
        ('checked ', 'Проверено'),
        ('rejected', 'Отклонено'),
    )

    card = models.ForeignKey('clients.Card', db_index=True, on_delete=models.CASCADE)
    type = models.ForeignKey(AchievementType, verbose_name='Тип достижения', db_index=True, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=ACHIEVEMENT_STATUS, blank=True, null=True, default=ACHIEVEMENT_STATUS[0][0], verbose_name='Статус достижения')
    document_number = models.CharField(max_length=255, blank=True, null=True, verbose_name='Номер документа')
    document_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата документа')

    def __str__(self):
        return f"{self.card} - {self.type.title}"

    @staticmethod
    def get_statuses() -> list[dict]:
        statuses = [{"id": status[0], "label": status[1]} for status in Achievement.ACHIEVEMENT_STATUS]
        return statuses

    class Meta:
        verbose_name = 'Достижение'
        verbose_name_plural = 'Достижения'


class SpecialRightsType(models.Model):
    title = models.CharField(max_length=255, verbose_name='Наименование типа особых прав', help_text='Инвалид, сирота, военнослужащий')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Тип особых прав'
        verbose_name_plural = 'Типы особых прав'


class SpecialRights(models.Model):
    title = models.CharField(max_length=255, verbose_name='Наименование особых прав', help_text='Инвалид 1ой группы')
    type = models.ForeignKey(SpecialRightsType, blank=True, null=True, verbose_name='Тип прав', db_index=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    @staticmethod
    def get_special_rights_tree():
        rights = SpecialRights.objects.all().prefetch_related('type')
        rights_dict = {}
        for i in rights:
            if rights_dict.get(i.type.title):
                rights_dict[i.type.title].append({"id": i.pk, "label": i.title})
            elif not rights_dict.get(i.type.title):
                rights_dict[i.type.title] = [{"id": i.pk, "label": i.title}]
        count = 0
        result_tree = []
        for key, value in rights_dict.items():
            result_tree.append({"id": f'а{+count}', "label": key, "children": value})
            count += 1
        return result_tree

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


class LogUpdateMMIS(models.Model):
    last_mmis_log_id = models.PositiveBigIntegerField(verbose_name='ID последнего лога в ММИС', blank=True, null=True)
    last_mmis_log_time = models.DateTimeField(verbose_name='Дата последнего лога в ММИС', blank=True, null=True)

    def __str__(self):
        return f"{self.last_mmis_log_id}-{self.last_mmis_log_time}"

    class Meta:
        verbose_name = 'Последний лог ММИС'
        verbose_name_plural = 'Последние логи ММИС'
