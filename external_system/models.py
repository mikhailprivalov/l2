from django.db import models


class FsliRefbookTest(models.Model):
    """
    Таблица справочников ФСЛИ: https://nsi.rosminzdrav.ru/#!/refbook/1.2.643.5.1.13.13.11.1080
    """
    code_fsli = models.CharField(max_length=20, db_index=True, help_text='Уникальный код ФСЛИ')
    code_loinc = models.CharField(max_length=20, help_text='Код LOINC')
    title = models.CharField(max_length=1000, db_index=True, help_text='Полное наименование')
    english_title = models.CharField(max_length=1000, help_text='Английское наименование')
    short_title = models.CharField(max_length=1000, help_text='Краткое наименование')
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
    sort_num = models.CharField(max_length=100, help_text='Порядок сортировки')
