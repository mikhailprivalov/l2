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
