from django.db import models


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
