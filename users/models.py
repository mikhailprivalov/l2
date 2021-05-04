import uuid

from django.contrib.auth.models import User
from django.db import models

from appconf.manager import SettingManager
from podrazdeleniya.models import Podrazdeleniya


class Speciality(models.Model):
    SPEC_TYPES = (
        (0, 'Консультации'),
        (1, 'Анестезиолог'),
    )

    title = models.CharField(max_length=255, help_text='Название')
    hide = models.BooleanField(help_text='Скрытие')
    spec_type = models.SmallIntegerField(choices=SPEC_TYPES, help_text='Тип специальности', default=0)
    rmis_id = models.PositiveSmallIntegerField(default=None, db_index=True, blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Специальность'
        verbose_name_plural = 'Специальности'


class DoctorProfile(models.Model):
    """
    Профили врачей
    """

    labtypes = (
        (0, "Не из лаборатории"),
        (1, "Врач"),
        (2, "Лаборант"),
    )
    user = models.OneToOneField(User, null=True, blank=True, help_text='Ссылка на Django-аккаунт', on_delete=models.CASCADE)
    specialities = models.ForeignKey(Speciality, blank=True, default=None, null=True, help_text='Специальности пользователя', on_delete=models.CASCADE)
    fio = models.CharField(max_length=255, help_text='ФИО')
    podrazdeleniye = models.ForeignKey(Podrazdeleniya, null=True, blank=True, help_text='Подразделение', db_index=True, on_delete=models.CASCADE)
    isLDAP_user = models.BooleanField(default=False, blank=True, help_text='Флаг, показывающий, что это импортированый из LDAP пользователь')
    labtype = models.IntegerField(choices=labtypes, default=0, blank=True, help_text='Категория профиля для лаборатории')
    login_id = models.UUIDField(null=True, default=None, blank=True, unique=True, help_text='Код авторизации')

    restricted_to_direct = models.ManyToManyField('directory.Researches', blank=True, help_text='Запрет на выдачу направлений с исследованиями')
    users_services = models.ManyToManyField('directory.Researches', related_name='users_services', blank=True, help_text='Услуги, оказываемые пользователем')
    personal_code = models.CharField(default='0', blank=True, max_length=5, help_text='Код врача для ТФОМС внутри МО')
    rmis_location = models.IntegerField(default=None, blank=True, null=True)
    local_location = models.CharField(default='', blank=True, null=True, max_length=20, help_text='Номера очередей (pk) через запятую', db_index=True)
    rmis_login = models.CharField(default='', blank=True, null=True, max_length=50, help_text='РМИС логин')
    rmis_password = models.CharField(default='', blank=True, null=True, max_length=50, help_text='РМИС пароль')
    rmis_resource_id = models.CharField(max_length=128, db_index=True, blank=True, default=None, null=True)
    rmis_employee_id = models.CharField(max_length=20, blank=True, default=None, null=True, help_text='РМИС employee id')
    rmis_service_id_time_table = models.CharField(max_length=20, blank=True, default=None, null=True, help_text='РМИС service id для расписания')

    hospital = models.ForeignKey('hospitals.Hospitals', db_index=True, blank=True, default=None, null=True, on_delete=models.SET_NULL)
    all_hospitals_users_control = models.BooleanField(default=False, blank=True, help_text="Может настраивать пользователей во всех организациях")
    eds_token = models.UUIDField(null=True, default=None, blank=True, unique=True, help_text='Токен для L2 EDS')

    def get_eds_token(self):
        if not self.eds_token:
            self.eds_token = uuid.uuid4()
            self.save(update_fields=['eds_token'])
        return str(self.eds_token)

    def get_hospital_id(self):
        hosp = self.get_hospital()
        if hosp:
            return hosp.pk
        return None

    def get_hospital(self):
        if not self.hospital:
            from hospitals.models import Hospitals

            self.hospital = Hospitals.get_default_hospital()
            self.save()
        return self.hospital

    def get_login_id(self):
        if not self.login_id:
            self.login_id = uuid.uuid4()
            self.save()
        c = '{:X>5}'.format(self.pk) + self.login_id.hex[:5]
        return c

    @property
    def hospital_safe_title(self):
        if not self.hospital:
            return SettingManager.get("org_title")
        return self.hospital.safe_short_title

    def get_fio(self, dots=True):
        """
        Функция формирования фамилии и инициалов (Иванов И.И.)
        :param dots:
        :return:
        """

        def gfl(w: str, dots):
            w = w.strip()
            if not w.isdigit() and len(w) > 0:
                w = w[0] + ("." if dots else "")
            return w

        fio = self.fio.strip().replace("  ", " ").strip()
        fio_split = fio.split(" ")

        if len(fio_split) == 0:
            return self.user.username
        if len(fio_split) == 1:
            return fio

        if len(fio_split) > 3:
            fio_split = [fio_split[0], " ".join(fio_split[1:-2]), fio_split[-1]]

        return fio_split[0] + " " + gfl(fio_split[1], dots) + ("" if len(fio_split) == 2 else gfl(fio_split[2], dots))

    def is_member(self, groups: list) -> bool:
        """
        Проверка вхождения пользователя в группу
        :param groups: названия групп
        :return: bool, входит ли в указаную группу
        """
        return self.user.groups.filter(name__in=groups).exists()

    def has_group(self, group) -> bool:
        return self.is_member([group])

    def get_data(self):
        return {"pk": self.pk, "fio": self.get_fio(), "username": self.user.username}

    def __str__(self):  # Получение фио при конвертации объекта DoctorProfile в строку
        if self.podrazdeleniye:
            return self.fio + ', ' + self.podrazdeleniye.title
        else:
            return self.fio

    class Meta:
        verbose_name = 'Профиль пользователя L2'
        verbose_name_plural = 'Профили пользователей L2'


class AssignmentTemplates(models.Model):
    title = models.CharField(max_length=40)
    doc = models.ForeignKey(DoctorProfile, null=True, blank=True, on_delete=models.CASCADE)
    podrazdeleniye = models.ForeignKey(Podrazdeleniya, null=True, blank=True, related_name='podr', on_delete=models.CASCADE)
    global_template = models.BooleanField(default=True, blank=True)

    def __str__(self):
        return (self.title + " | Шаблон для ") + (str(self.doc) if self.doc else str(self.podrazdeleniye) if self.podrazdeleniye else "всех")

    class Meta:
        verbose_name = 'Шаблон назначений'
        verbose_name_plural = 'Шаблоны назначений'


class AssignmentResearches(models.Model):
    template = models.ForeignKey(AssignmentTemplates, on_delete=models.CASCADE)
    research = models.ForeignKey('directory.Researches', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.template) + "  | " + str(self.research)

    class Meta:
        verbose_name = 'Исследование для шаблона назначений'
        verbose_name_plural = 'Исследования для шаблонов назначений'
