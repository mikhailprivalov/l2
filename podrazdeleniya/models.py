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
    CASE = 16
    COMPLEX = 18

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
        (CASE, "Случаи"),
        (COMPLEX, "Комплексные услуги"),
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
    nsi_title = models.CharField(max_length=255, default='', blank=True, help_text='по ФРМО')
    hospital = models.ForeignKey('hospitals.Hospitals', db_index=True, blank=True, default=None, null=True, on_delete=models.SET_NULL)
    ecp_code = models.CharField(max_length=16, default="", blank=True, verbose_name="Код для ECP")
    n3_id = models.CharField(max_length=40, help_text='N3_ID', blank=True, default="")
    print_additional_page_direction = models.CharField(max_length=255, default="", blank=True, verbose_name="Дополнительные формы при печати направления для подразделения")
    profile_ecp_code = models.CharField(max_length=16, default="", blank=True, verbose_name="Профиль отделения код ecp")
    hosp_research_default = models.ForeignKey(
        'directory.Researches', blank=True, default=None, null=True, verbose_name="Услуга стационара по котрой по умолчанию подгружаются шаблоны", on_delete=models.CASCADE
    )

    def get_title(self):
        return self.short_title or self.title

    @staticmethod
    def get_podrazdeleniya(p_type: int):
        result = [{"id": podrazdelenie.pk, "label": podrazdelenie.title} for podrazdelenie in Podrazdeleniya.objects.filter(p_type=p_type).order_by('title')]
        return result

    @staticmethod
    def get_all_departments(exclude=None):
        type_exclude = [0]
        if exclude:
            type_exclude.extend(exclude)
        result = [{"id": podrazdelenie.pk, "label": podrazdelenie.title} for podrazdelenie in Podrazdeleniya.objects.all().exclude(p_type__in=type_exclude).order_by('title')]
        return result

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
    podrazdeleniye = models.ForeignKey(Podrazdeleniya, null=True, blank=True, help_text='Подразделение', db_index=True, on_delete=models.CASCADE)
    is_card_storage = models.BooleanField(default=False, blank=True, db_index=True, verbose_name='Картохранилище')

    def __str__(self):
        return f"{self.hospital} — {self.title}"

    class Meta:
        verbose_name = 'Кабинет'
        verbose_name_plural = 'Кабинеты'
        ordering = ['-id']


class Chamber(models.Model):
    podrazdelenie = models.ForeignKey(Podrazdeleniya, on_delete=models.CASCADE)
    title = models.CharField(max_length=64, help_text='Название палаты')

    def __str__(self):
        return f'{self.podrazdelenie} {self.title}'

    class Meta:
        verbose_name = 'Палата'
        verbose_name_plural = 'Палаты'

    @staticmethod
    def check_user(user, need_department_id):
        has_group = user.doctorprofile.has_group("Палаты: все подразделения")
        if user.doctorprofile.podrazdelenie_id == need_department_id:
            result = True
        elif has_group:
            result = True
        else:
            result = user.is_superuser
        return result


class Bed(models.Model):
    chamber = models.ForeignKey(Chamber, on_delete=models.CASCADE)
    bed_number = models.PositiveSmallIntegerField(help_text="Номер койки")

    def __str__(self):
        return f'{self.chamber} - {self.bed_number}'

    class Meta:
        verbose_name = 'Койка'
        verbose_name_plural = 'Койки'


class PatientToBed(models.Model):
    direction = models.ForeignKey("directions.Napravleniya", db_index=True, on_delete=models.CASCADE)
    doctor = models.ForeignKey("users.DoctorProfile", db_index=True, on_delete=models.CASCADE, null=True)
    bed = models.ForeignKey(Bed, db_index=True, on_delete=models.CASCADE)
    date_in = models.DateField(auto_now_add=True)
    date_out = models.DateField(null=True)

    def __str__(self):
        return f'{self.direction.client.individual.fio()}'

    @staticmethod
    def update_doctor(doctor_id, direction_id, is_assign, user):
        result = {"ok": True, "message": ""}
        patient_to_bed = PatientToBed.objects.filter(direction_id=direction_id, date_out=None).select_related('bed__chamber').first()
        bed_department_id = patient_to_bed.bed.chamber.podrazdelenie_id
        user_can_edit = Chamber.check_user(user, bed_department_id)
        if not user_can_edit:
            result = {"ok": False, "message": "Пользователь не принадлежит к данному подразделению"}
            return result
        if is_assign:
            patient_to_bed.doctor_id = doctor_id
            patient_to_bed.save()
        else:
            patient_to_bed.doctor = None
            patient_to_bed.save()
        return result

    class Meta:
        verbose_name = 'Историю коек'
        verbose_name_plural = 'История коек'


class PatientStationarWithoutBeds(models.Model):
    direction = models.ForeignKey("directions.Napravleniya", db_index=True, on_delete=models.CASCADE)
    department = models.ForeignKey(Podrazdeleniya, db_index=True, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f'{self.direction.client.individual.fio()}'

    class Meta:
        verbose_name = 'Пациент без койки'
        verbose_name_plural = 'Пациенты без коек'
