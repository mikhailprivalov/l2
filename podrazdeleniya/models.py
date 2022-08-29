from django.db import models


class Podrazdeleniya(models.Model):  # Модель подразделений
    HIDDEN = 0
    DEPARTMENT = 1
    LABORATORY = 2
    PARACLINIC = 3
    DOCREFFERALS = 4
    TREATMENT = 5
    STOM = 6
    HOSP = 7
    MICROBIOLOGY = 8
    MORFOLOGY = 10000  # Не добавлять в типы
    FORMS = 11
    DIRECTIONPARAMS = 12
    APPLICATIONS = 13
    MONITORINGS = 14

    TYPES = (
        (HIDDEN, "Скрыто"),
        (DEPARTMENT, "Направляющее отделение"),
        (LABORATORY, "Лаборатория"),
        (PARACLINIC, "Параклиника"),
        (DOCREFFERALS, "Консультации"),
        (TREATMENT, "Лечение"),
        (STOM, "Стоматология"),
        (HOSP, "Стационар"),
        (MICROBIOLOGY, "Микробиология"),
        (FORMS, "Формы"),
        (DIRECTIONPARAMS, "Параметры для направления"),
        (APPLICATIONS, "Заявления"),
        (MONITORINGS, "Мониторинги"),
    )

    ODII_TYPES = (
        (1, 'Компьютерная томография'),
        (2, 'Магнитно-резонансная томография'),
        (3, 'Ультразвуковая диагностика'),
        (4, 'Рентгенологическая диагностика'),
        (5, 'Радионуклидная диагностика'),
        (6, 'Функциональная диагностика'),
        (7, 'Эндоскопия'),
    )

    title = models.CharField(max_length=255)  # Название подразделения
    short_title = models.CharField(max_length=50, default='', blank=True)
    hide = models.BooleanField(default=False, blank=True, db_index=True)  # DEPRECATED. True=Скрывать подразделение
    vaccine = models.BooleanField(default=False, blank=True)
    p_type = models.PositiveSmallIntegerField(choices=TYPES, default=HIDDEN, blank=True)
    rmis_id = models.CharField(max_length=15, default=None, blank=True, null=True)
    rmis_direction_type = models.CharField(max_length=255, default="Направление в лабораторию", blank=True)
    rmis_department_title = models.CharField(max_length=255, default="Клинико-диагностическая лаборатория (КДЛ)", blank=True)
    can_has_pacs = models.BooleanField(default=False, blank=True)
    odii_type = models.PositiveSmallIntegerField(choices=ODII_TYPES, default=None, null=True, blank=True, help_text="Оказываемые виды инструментальных услуг")
    oid = models.CharField(max_length=55, default="", blank=True, help_text='OID подразделения')
    nsi_title = models.CharField(max_length=50, default='', blank=True, help_text='по ФРМО')
    hospital = models.ForeignKey('hospitals.Hospitals', db_index=True, blank=True, default=None, null=True, on_delete=models.SET_NULL)
    ecp_code = models.CharField(max_length=16, default="", blank=True, verbose_name="Код для ECP")
    n3_id = models.CharField(max_length=40, help_text='N3_ID', blank=True, default="")

    def get_title(self):
        return self.short_title or self.title

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'
        ordering = ['-id']


class Room(models.Model):
    COMMON = 0
    BIOMATERIAL_GET = 1

    TYPES = (
        (COMMON, 'Общий'),
        (BIOMATERIAL_GET, 'Забор материала'),
    )

    hospital = models.ForeignKey('hospitals.Hospitals', db_index=True, verbose_name='Больница', on_delete=models.CASCADE)
    title = models.CharField(max_length=64, verbose_name='Название кабинета')
    type = models.PositiveSmallIntegerField(choices=TYPES, default=COMMON, db_index=True, verbose_name='Тип')
    hide = models.BooleanField(default=False, blank=True, db_index=True, verbose_name='Скрыть')

    def __str__(self):
        return f"{self.hospital} — {self.title}"

    class Meta:
        verbose_name = 'Кабинет'
        verbose_name_plural = 'Кабинеты'
        ordering = ['-id']
