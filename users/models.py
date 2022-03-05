import uuid

from django.contrib.auth.models import User, Group
from django.db import models

from appconf.manager import SettingManager
from laboratory.settings import EMAIL_HOST
from podrazdeleniya.models import Podrazdeleniya
from users.tasks import send_login, send_new_email_code, send_new_password, send_old_email_code


class Speciality(models.Model):
    SPEC_TYPES = (
        (0, 'Консультации'),
        (1, 'Анестезиолог'),
    )

    title = models.CharField(max_length=255, help_text='Название')
    hide = models.BooleanField(help_text='Скрытие', default=False)
    spec_type = models.SmallIntegerField(choices=SPEC_TYPES, help_text='Тип специальности', default=0)
    rmis_id = models.PositiveSmallIntegerField(default=None, db_index=True, blank=True, null=True)
    n3_id = models.PositiveSmallIntegerField(default=None, db_index=True, blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Специальность'
        verbose_name_plural = 'Специальности'


def add_dots_if_not_digit(w: str, dots):
    w = w.strip()
    if not w:
        return ''
    if not w.isdigit() and len(w) > 0:
        w = w[0] + ("." if dots else "")
    return w


class Position(models.Model):
    title = models.CharField(max_length=255, help_text='Название')
    hide = models.BooleanField(help_text='Скрытие', default=False)
    rmis_id = models.PositiveSmallIntegerField(default=None, db_index=True, blank=True, null=True)
    n3_id = models.PositiveSmallIntegerField(default=None, db_index=True, blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должность'


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
    fio = models.CharField(max_length=255, help_text='ФИО')  # DEPRECATED
    family = models.CharField(max_length=255, help_text='Фамилия', blank=True, default=None, null=True)
    name = models.CharField(max_length=255, help_text='Имя', blank=True, default=None, null=True)
    patronymic = models.CharField(max_length=255, help_text='Отчество', blank=True, default=None, null=True)
    email = models.EmailField(max_length=255, blank=True, default=None, null=True, help_text='Email пользователя')
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
    white_list_monitoring = models.ManyToManyField('directory.Researches', related_name='white_list_monitoring', blank=True, help_text='Доступные для просмотра мониторинги')
    black_list_monitoring = models.ManyToManyField('directory.Researches', related_name='black_list_monitoring', blank=True, help_text='Запрещены для просмотра мониторинги')
    position = models.ForeignKey(Position, blank=True, default=None, null=True, help_text='Должность пользователя', on_delete=models.SET_NULL)
    snils = models.CharField(max_length=11, help_text='СНИЛС', blank=True, default="", db_index=True)
    n3_id = models.CharField(max_length=40, help_text='N3_ID', blank=True, default="")
    disabled_forms = models.CharField(max_length=255, help_text='Отключеные формы перчислить ч/з запятую', blank=True, default="")
    disabled_statistic_categories = models.CharField(max_length=255, help_text='Отключить доступ к статистике-категории ч/з запятую', blank=True, default="")
    disabled_statistic_reports = models.CharField(max_length=255, help_text='Отключить доступ к статистике категории-отчету ч/з запятую', blank=True, default="")
    disabled_fin_source = models.ManyToManyField("directions.IstochnikiFinansirovaniya", blank=True, help_text='Запрещеные источники финансирвоания')
    external_access = models.BooleanField(default=False, blank=True, help_text='Разрешен внешний доступ')
    date_stop_external_access = models.DateField(help_text='Окончание внешнего доступа', db_index=True, default=None, blank=True, null=True)

    def reset_password(self):
        if not self.user or not self.email or not EMAIL_HOST:
            return False

        new_password = User.objects.make_random_password()

        self.user.set_password(new_password)
        self.user.save()

        send_new_password.delay(
            self.email,
            self.user.username,
            new_password,
            self.hospital_safe_title
        )

        return True

    def register_login(self, ip: str):
        if not self.user or not self.email or not EMAIL_HOST:
            return

        send_login.delay(
            self.email,
            self.user.username,
            ip,
            self.hospital_safe_title
        )

    def old_email_send_code(self, request):
        if not self.user or not EMAIL_HOST:
            return
        request.session['old_email_code'] = User.objects.make_random_password()

        send_old_email_code.delay(
            self.email,
            self.user.username,
            request.session['old_email_code'],
            self.hospital_safe_title
        )

    def check_old_email_code(self, code: str, request):
        if not self.user:
            return False

        if not self.email:
            return True

        if not code:
            return False

        return code == request.session.get('old_email_code')

    def new_email_send_code(self, new_email: str, request):
        if not self.user or not EMAIL_HOST:
            return
        request.session['new_email'] = new_email
        request.session['new_email_code'] = User.objects.make_random_password()

        send_new_email_code.delay(
            new_email,
            self.user.username,
            request.session['new_email_code'],
            self.hospital_safe_title
        )

    def new_email_check_code(self, new_email: str, code: str, request):
        if not self.user or not code or not new_email:
            return False

        return request.session.get('new_email') == new_email and code == request.session.get('new_email_code')

    def set_new_email(self, new_email: str,request):
        self.email = new_email
        self.save(update_fields=['email'])
        request.session['new_email'] = None
        request.session['new_email_code'] = None

    @property
    def dict_data(self):
        return {
            "snils": self.snils,
            "speciality": self.specialities.n3_id if self.specialities else None,
            "position": self.position.n3_id if self.position else None,
            "family": self.family,
            "name": self.name,
            "patronymic": self.patronymic,
        }

    @property
    def uploading_data(self):
        return {
            "pk": self.pk,
            "n3Id": self.n3_id,
            "spec": self.specialities.n3_id if self.specialities else None,
            "role": self.position.n3_id if self.position else None,
            **self.dict_data,
        }

    @property
    def get_disabled_fin_source(self):
        return self.disabled_fin_source

    def get_eds_allowed_sign(self):
        ret = []
        doc_groups = ("Врач параклиники", "Врач консультаций", 'Врач-лаборант')
        if any([self.has_group(x) for x in doc_groups]):
            ret.append('Врач')
        if self.has_group('ЭЦП Медицинской организации'):
            ret.append('Медицинская организация')
        return ret

    def get_hospital_id(self):
        hosp = self.get_hospital()
        if hosp:
            return hosp.pk
        return None

    def get_hospital_title(self):
        hosp = self.get_hospital()
        if hosp:
            return hosp.safe_short_title
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

    def get_fio_parts(self):
        if not self.family or not self.name or not self.patronymic:
            fio = self.fio.strip().replace("  ", " ").strip()
            fio_split = fio.split(" ")
            if len(fio_split) > 3:
                fio_split = [fio_split[0], " ".join(fio_split[1:-2]), fio_split[-1]]
            fio_split += [''] * max(0, 3 - len(fio_split))
            self.family = fio_split[0]
            self.name = fio_split[1]
            self.patronymic = fio_split[2]
            self.save(update_fields=['family', 'name', 'patronymic'])
        return self.family, self.name, self.patronymic

    def get_full_fio(self):
        return " ".join(self.get_fio_parts())

    def get_fio(self, dots=True):
        """
        Функция формирования фамилии и инициалов (Иванов И.И.)
        :param dots:
        :return:
        """
        fio_parts = self.get_fio_parts()

        return f"{fio_parts[0]} {add_dots_if_not_digit(fio_parts[1], dots)} {add_dots_if_not_digit(fio_parts[2], dots)}".strip()

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

    def get_position(self):
        if self.position:
            return self.position.title
        return None

    def __str__(self):  # Получение фио при конвертации объекта DoctorProfile в строку
        if self.podrazdeleniye:
            return self.get_full_fio() + ', ' + self.podrazdeleniye.title
        else:
            return self.get_full_fio()

    class Meta:
        verbose_name = 'Профиль пользователя L2'
        verbose_name_plural = 'Профили пользователей L2'


class AssignmentTemplates(models.Model):
    SHOW_TYPES_SITE_TYPES_TYPE = {
        'consult': 0,
        'treatment': 1,
        'stom': 2,
        'hospital': 2,
        'microbiology': 4,
    }

    title = models.CharField(max_length=40)
    doc = models.ForeignKey(DoctorProfile, null=True, blank=True, on_delete=models.CASCADE)
    podrazdeleniye = models.ForeignKey(Podrazdeleniya, null=True, blank=True, related_name='podr', on_delete=models.CASCADE)
    global_template = models.BooleanField(default=True, blank=True)

    show_in_research_picker = models.BooleanField(default=False, blank=True)
    podrazdeleniye = models.ForeignKey(Podrazdeleniya, related_name="template_department", help_text="Лаборатория",
                                       db_index=True, null=True, blank=True, default=None, on_delete=models.CASCADE)
    is_paraclinic = models.BooleanField(default=False, blank=True, help_text="Это параклинический шаблон", db_index=True)
    is_doc_refferal = models.BooleanField(default=False, blank=True, help_text="Это исследование-направление шаблон к врачу", db_index=True)
    is_treatment = models.BooleanField(default=False, blank=True, help_text="Это лечение — шаблон", db_index=True)
    is_stom = models.BooleanField(default=False, blank=True, help_text="Это стоматология — шаблон", db_index=True)
    is_hospital = models.BooleanField(default=False, blank=True, help_text="Это стационар — шаблон", db_index=True)
    is_microbiology = models.BooleanField(default=False, blank=True, help_text="Это микробиологический шаблон", db_index=True)
    is_citology = models.BooleanField(default=False, blank=True, help_text="Это цитологический шаблон", db_index=True)
    is_gistology = models.BooleanField(default=False, blank=True, help_text="Это гистологический шаблон", db_index=True)
    site_type = models.ForeignKey("directory.ResearchSite", related_name='site_type_in_template', default=None, null=True, blank=True, help_text='Место услуги', on_delete=models.SET_NULL,
                                  db_index=True)

    def get_show_type(self):
        if self.is_paraclinic:
            return 'paraclinic'
        if self.is_doc_refferal:
            return 'consult'
        if self.is_treatment:
            return 'treatment'
        if self.is_stom:
            return 'stom'
        if self.is_hospital:
            return 'hospital'
        if self.is_microbiology:
            return 'microbiology'
        if self.is_citology:
            return 'citology'
        if self.is_gistology:
            return 'gistology'
        if self.podrazdeleniye:
            return 'lab'
        return 'unknown'

    @property
    def reversed_type(self):
        if self.is_treatment:
            return -3
        if self.is_stom:
            return -4
        if self.is_hospital:
            return -5
        if self.is_microbiology or self.is_citology or self.is_gistology:
            return 2 - Podrazdeleniya.MORFOLOGY
        return self.podrazdeleniye_id or -2

    def get_site_type_id(self):
        if self.is_microbiology:
            return Podrazdeleniya.MORFOLOGY + 1
        if self.is_citology:
            return Podrazdeleniya.MORFOLOGY + 2
        if self.is_gistology:
            return Podrazdeleniya.MORFOLOGY + 3
        return self.site_type_id

    def as_research(self):
        r = self
        return {
            "pk": f'template-{r.pk}',
            "onlywith": -1,
            "department_pk": r.reversed_type,
            "title": r.title,
            "full_title": r.title,
            "doc_refferal": r.is_doc_refferal,
            "treatment": r.is_treatment,
            "is_hospital": r.is_hospital,
            "is_form": False,
            "is_application": False,
            "stom": r.is_stom,
            "need_vich_code": False,
            "comment_variants": [],
            "autoadd": list(AssignmentResearches.objects.filter(template=r).values_list('research_id', flat=True)),
            "auto_deselect": True,
            "addto": [],
            "code": '',
            "type": "4" if not r.podrazdeleniye else str(r.podrazdeleniye.p_type),
            "site_type": r.get_site_type_id(),
            "site_type_raw": r.site_type_id,
            "localizations": [],
            "service_locations": [],
            "direction_params": -1,
            "research_data": {'research': {'status': 'NOT_LOADED'}},
        }

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


class AvailableResearchByGroup(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    research = models.ForeignKey('directory.Researches', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.group) + "  | " + str(self.research)

    class Meta:
        unique_together = ('group', 'research')
        verbose_name = 'Услуга для групп'
        verbose_name_plural = 'Услуги для групп'
