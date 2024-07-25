import os
import random
import string
import uuid

import pyotp
from django.contrib.auth.models import User, Group
from django.db import models, transaction
from django.utils import timezone
from django.core.cache import cache

from appconf.manager import SettingManager
from laboratory.redis import get_redis_client
from laboratory.settings import EMAIL_HOST, MEDIA_ROOT
from podrazdeleniya.models import Podrazdeleniya
from users.tasks import send_login, send_new_email_code, send_new_password, send_old_email_code
from utils.string import make_short_name_form


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


class Position(models.Model):
    title = models.CharField(max_length=255, help_text='Название')
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
    totp_secret = models.CharField(max_length=64, blank=True, default=None, null=True, help_text='Секретный ключ для двухфакторной авторизации')
    family = models.CharField(max_length=255, help_text='Фамилия', blank=True, default=None, null=True)
    name = models.CharField(max_length=255, help_text='Имя', blank=True, default=None, null=True)
    patronymic = models.CharField(max_length=255, help_text='Отчество', blank=True, default=None, null=True)
    email = models.EmailField(max_length=255, blank=True, default=None, null=True, help_text='Email пользователя')
    podrazdeleniye = models.ForeignKey(Podrazdeleniya, null=True, blank=True, help_text='Подразделение', db_index=True, on_delete=models.CASCADE)
    labtype = models.IntegerField(choices=labtypes, default=0, blank=True, help_text='Категория профиля для лаборатории')
    login_id = models.UUIDField(null=True, default=None, blank=True, unique=True, help_text='Код авторизации')
    restricted_to_direct = models.ManyToManyField('directory.Researches', blank=True, help_text='Запрет на выдачу направлений с исследованиями')
    users_services = models.ManyToManyField('directory.Researches', related_name='users_services', blank=True, help_text='Услуги, оказываемые пользователем')
    personal_code = models.CharField(default='0', blank=True, max_length=5, help_text='Код врача для ТФОМС внутри МО')
    rmis_location_deprecated = models.IntegerField(default=None, blank=True, null=True)
    local_location = models.CharField(default='', blank=True, null=True, max_length=20, help_text='Номера очередей (pk) через запятую', db_index=True)
    rmis_login = models.CharField(default='', blank=True, null=True, max_length=50, help_text='РМИС логин')
    rmis_password = models.CharField(default='', blank=True, null=True, max_length=50, help_text='РМИС пароль')
    rmis_resource_id = models.CharField(max_length=128, db_index=True, blank=True, default=None, null=True)
    rmis_location = models.CharField(max_length=128, db_index=True, blank=True, default=None, null=True)
    rmis_employee_id = models.CharField(max_length=20, blank=True, default=None, null=True, help_text='РМИС employee id')
    rmis_service_id_time_table = models.CharField(max_length=20, blank=True, default=None, null=True, help_text='РМИС service id для расписания')
    hospital = models.ForeignKey('hospitals.Hospitals', db_index=True, blank=True, default=None, null=True, on_delete=models.SET_NULL)
    all_hospitals_users_control = models.BooleanField(default=False, blank=True, help_text="Может настраивать пользователей во всех организациях")
    white_list_monitoring = models.ManyToManyField('directory.Researches', related_name='white_list_monitoring', blank=True, help_text='Доступные для просмотра мониторинги')
    black_list_monitoring = models.ManyToManyField('directory.Researches', related_name='black_list_monitoring', blank=True, help_text='Запрещены для просмотра мониторинги')
    position = models.ForeignKey(Position, blank=True, default=None, null=True, help_text='Должность пользователя', on_delete=models.SET_NULL)
    snils = models.CharField(max_length=11, help_text='СНИЛС', blank=True, default="", db_index=True)
    n3_id = models.CharField(max_length=40, help_text='N3_ID', blank=True, default="")
    disabled_forms = models.CharField(max_length=255, help_text='Отключенные формы перчислить ч/з запятую', blank=True, default="")
    disabled_statistic_categories = models.CharField(max_length=255, help_text='Отключить доступ к статистике-категории ч/з запятую', blank=True, default="")
    disabled_statistic_reports = models.CharField(max_length=255, help_text='Отключить доступ к статистике категории-отчету ч/з запятую', blank=True, default="")
    disabled_fin_source = models.ManyToManyField("directions.IstochnikiFinansirovaniya", blank=True, help_text='Запрещенные источники финансирования')
    external_access = models.BooleanField(default=False, blank=True, help_text='Разрешен внешний доступ')
    date_stop_external_access = models.DateField(help_text='Окончание внешнего доступа', db_index=True, default=None, blank=True, null=True)
    district_group = models.ForeignKey('clients.District', blank=True, default=None, null=True, help_text='Участковая служба', on_delete=models.CASCADE)
    not_control_anketa = models.BooleanField(default=False, blank=True, help_text='Не контролировать заполнение Анкет')
    signature_stamp_pdf = models.CharField(max_length=255, blank=True, null=True, default=None, help_text="Ссылка на файл подписи pdf")
    last_online = models.DateTimeField(default=None, blank=True, null=True, help_text="Когда пользователь был в сети")
    cabinet = models.CharField(max_length=255, blank=True, null=True, default=None, help_text="Кабинет приема")
    max_age_patient_registration = models.SmallIntegerField(help_text='Ограничения возраста записи указать в месяцах', default=-1)
    available_quotas_time = models.TextField(default='', blank=True, help_text='Доступная запись для подразделений по времени {"id-подразделения": "10:00-15:00"}')
    is_system_user = models.BooleanField(default=False, blank=True)
    room_access = models.ManyToManyField('podrazdeleniya.Room', blank=True, help_text='Доступ к кабинетам')
    date_extract_employee = models.DateField(help_text='Дата выписки запрошена', db_index=True, default=None, blank=True, null=True)
    date_stop_certificate = models.DateField(help_text='Дата окончания сертификата', db_index=True, default=None, blank=True, null=True)
    replace_doctor_cda = models.ForeignKey('self', related_name='used_doctor_cda', help_text="Замена доктора для cda", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    additional_info = models.TextField(default='', blank=True, help_text='Дополнительная информация описывать словарем {}')
    hosp_research_template = models.ForeignKey(
        'directory.Researches',
        related_name='hosp_research_template',
        blank=True,
        default=None,
        null=True,
        verbose_name="Услуга стационара по котрой по умолчанию подгружаются шаблоны",
        on_delete=models.CASCADE,
    )

    @staticmethod
    def get_system_profile():
        doc = DoctorProfile.objects.filter(is_system_user=True).first()

        if not doc:
            user = User.objects.create_user(uuid.uuid4().hex)
            user.is_active = True
            user.save()
            doc = DoctorProfile(user=user, fio='Системный Пользователь', is_system_user=True)
            doc.save()
            doc.get_fio_parts()

        return doc

    @property
    def notify_queue_key_base(self):
        return f"chats:notify-queues:{self.pk}"

    def get_notify_queue_key(self, suffix):
        return f"{self.notify_queue_key_base}:{suffix}"

    def get_notify_queue_key_list(self, suffix):
        return f"queue:{self.notify_queue_key_base}:{suffix}"

    @property
    def online_key(self):
        return f"chats:online-status:{self.pk}"

    @property
    def messages_count_key(self):
        return f"chats:messages:{self.pk}"

    def create_notify_queue_token(self):
        redis_client = get_redis_client()
        if not redis_client:
            return None
        token = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        key = self.get_notify_queue_key(token)

        redis_client.set(key, 1, ex=60)

        return token

    def update_notify_queue_token(self, token):
        redis_client = get_redis_client()
        if not redis_client:
            return
        key = self.get_notify_queue_key(token)
        redis_client.expire(key, 60)

    def check_or_make_new_notify_queue_token(self, token):
        redis_client = get_redis_client()
        if not redis_client:
            return 'empty'
        if token:
            key = self.get_notify_queue_key(token)
            if not redis_client.exists(key):
                return self.create_notify_queue_token()
            else:
                self.update_notify_queue_token(token)
                return token
        token = self.create_notify_queue_token()
        return token

    def get_all_notify_queues(self):
        redis_client = get_redis_client()
        if not redis_client:
            return []
        keys = redis_client.keys(self.get_notify_queue_key("*"))
        return [f"queue:{key.decode('utf-8')}" for key in keys]

    def add_message_id_to_queues(self, message_id):
        redis_client = get_redis_client()
        if not redis_client:
            return
        for key in self.get_all_notify_queues():
            redis_client.lpush(key, message_id)

    def get_messages_from_queue_by_token(self, token):
        redis_client = get_redis_client()
        if not redis_client:
            return []
        key = self.get_notify_queue_key_list(token)
        messages = redis_client.lrange(key, 0, -1)
        redis_client.delete(key)

        keys = self.get_all_notify_queues()
        keys_queues = [x.decode('utf-8') for x in redis_client.keys(self.get_notify_queue_key_list("*"))]
        for key in keys_queues:
            if key not in keys:
                redis_client.delete(key)

        return messages

    def mark_as_online(self):
        self.last_online = timezone.now()
        self.save(update_fields=('last_online',))
        cache.set(self.online_key, True, 100)

    def mark_as_offline(self):
        cache.delete(self.online_key)
        hospital = self.get_hospital()
        cache_key = f"chats:users-by-departments:{hospital.pk}"
        cache.delete(cache_key)

    def inc_messages_count(self):
        redis_client = get_redis_client()
        if redis_client:
            redis_client.incr(self.messages_count_key)

    def get_messages_count(self):
        redis_client = get_redis_client()
        if redis_client:
            return int(redis_client.get(self.messages_count_key) or 0)
        return 0

    def get_is_online(self):
        return cache.get(self.online_key) or False

    def get_dialog_data(self):
        is_online = self.get_is_online()

        return {
            "id": self.pk,
            "name": self.get_full_fio(),
            "isOnline": is_online,
            "lastOnline": self.get_last_online(),
            "position": self.get_position(),
            "speciality": self.get_speciality(),
        }

    def get_signature_stamp_pdf(self):
        if self.signature_stamp_pdf:
            return os.path.join(MEDIA_ROOT, 'docprofile_stamp_pdf', self.signature_stamp_pdf)
        return None

    def reset_password(self):
        if not self.user or not self.email or not EMAIL_HOST:
            return False

        new_password = User.objects.make_random_password()

        self.user.set_password(new_password)
        self.user.save()

        send_new_password.delay(self.email, self.user.username, new_password, self.hospital_safe_title)

        return True

    def register_login(self, ip: str):
        self.mark_as_online()
        hospital = self.get_hospital()

        cache_key = f"chats:users-by-departments:{hospital.pk}"
        cache.delete(cache_key)

        if not self.user or not self.email or not EMAIL_HOST:
            return

        send_login.delay(self.email, self.user.username, ip, self.hospital_safe_title)

    def old_email_send_code(self, request):
        if not self.user or not EMAIL_HOST:
            return
        request.session['old_email_code'] = User.objects.make_random_password()

        send_old_email_code.delay(self.email, self.user.username, request.session['old_email_code'], self.hospital_safe_title)

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

        send_new_email_code.delay(new_email, self.user.username, request.session['new_email_code'], self.hospital_safe_title)

    def new_email_check_code(self, new_email: str, code: str, request):
        if not self.user or not code or not new_email:
            return False

        return request.session.get('new_email') == new_email and code == request.session.get('new_email_code')

    def set_new_email(self, new_email: str, request):
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
            "positionCode": self.position.n3_id if self.position else None,
            "positionName": self.position.title if self.position else None,
            "family": self.family,
            "name": self.name,
            "patronymic": self.patronymic,
        }

    @property
    def uploading_data(self):
        return {
            "id": self.pk,
            "pk": self.pk,
            "n3Id": self.n3_id,
            "externalId": self.rmis_employee_id,
            "spec": self.specialities.n3_id if self.specialities else None,
            "role": self.position.n3_id if self.position else None,
            "podrazdeleniyeEcpCode": self.podrazdeleniye.ecp_code if self.podrazdeleniye else None,
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

    def get_hospital_full_id(self):
        from hospitals.models import Hospitals

        hosps = [
            Hospitals.get_default_hospital(),
            self.get_hospital(),
        ]

        parts = []
        for hosp in hosps:
            if hosp:
                if hosp.oid:
                    parts.append(hosp.oid)
                elif hosp.code_tfoms:
                    parts.append(hosp.code_tfoms)
                else:
                    parts.append(hosp.n3_id)
                parts.append(hosp.pk)
            else:
                parts.append(-1)

        return '/'.join([str(x) for x in parts])

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
        return " ".join(self.get_fio_parts()).strip()

    def get_fio(self, dots=True, with_space=True):
        """
        Функция формирования фамилии и инициалов (Иванов И.И.)
        :param dots:
        :return:
        """
        fio_parts = self.get_fio_parts()

        return make_short_name_form(fio_parts[0], fio_parts[1], fio_parts[2], dots, with_space)

    def is_member(self, groups: list) -> bool:
        """
        Проверка вхождения пользователя в группу
        :param groups: названия групп
        :return: bool, входит ли в указанную группу
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

    def get_speciality(self):
        if self.specialities:
            return self.specialities.title
        return None

    def get_last_online(self):
        if self.last_online:
            return int(self.last_online.timestamp())
        return None

    def check_totp(self, code, ip):
        if not self.totp_secret:
            return True
        key = f"{self.pk}:{code}"
        prev_ip = cache.get(key)
        if prev_ip and prev_ip != ip:
            return False
        cache.set(key, ip, 60)
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(code)

    @staticmethod
    def getCashRegisterData():
        return {"id": 1, "title": "dsf", "shiftId": 1}

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
    podrazdeleniye = models.ForeignKey(
        Podrazdeleniya, related_name="template_department", help_text="Лаборатория", db_index=True, null=True, blank=True, default=None, on_delete=models.CASCADE
    )
    is_paraclinic = models.BooleanField(default=False, blank=True, help_text="Это параклинический шаблон", db_index=True)
    is_doc_refferal = models.BooleanField(default=False, blank=True, help_text="Это исследование-направление шаблон к врачу", db_index=True)
    is_treatment = models.BooleanField(default=False, blank=True, help_text="Это лечение — шаблон", db_index=True)
    is_stom = models.BooleanField(default=False, blank=True, help_text="Это стоматология — шаблон", db_index=True)
    is_hospital = models.BooleanField(default=False, blank=True, help_text="Это стационар — шаблон", db_index=True)
    is_microbiology = models.BooleanField(default=False, blank=True, help_text="Это микробиологический шаблон", db_index=True)
    is_citology = models.BooleanField(default=False, blank=True, help_text="Это цитологический шаблон", db_index=True)
    is_gistology = models.BooleanField(default=False, blank=True, help_text="Это гистологический шаблон", db_index=True)
    site_type = models.ForeignKey(
        "directory.ResearchSite", related_name='site_type_in_template', default=None, null=True, blank=True, help_text='Место услуги', on_delete=models.SET_NULL, db_index=True
    )

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

    @staticmethod
    def get_researches_by_template(template_pks):
        template_reearches = AssignmentResearches.objects.filter(template_id__in=template_pks)
        return [i.research_id for i in template_reearches]


class AvailableResearchByGroup(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    research = models.ForeignKey('directory.Researches', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.group) + "  | " + str(self.research)

    class Meta:
        unique_together = ('group', 'research')
        verbose_name = 'Услуга для групп'
        verbose_name_plural = 'Услуги для групп'


class DistrictResearchLimitAssign(models.Model):
    PERIOD_TYPES = (
        (0, 'День'),
        (1, 'Месяц'),
    )
    district_group = models.ForeignKey('clients.District', blank=True, default=None, null=True, help_text='Участковая служба', on_delete=models.CASCADE)
    research = models.ForeignKey('directory.Researches', related_name='услуга', blank=True, default=None, null=True, help_text='Услуга', on_delete=models.CASCADE)
    limit_count = models.PositiveSmallIntegerField(default=None, blank=True, null=True)
    type_period_limit = models.SmallIntegerField(choices=PERIOD_TYPES, help_text='Тип ограничения на период', default=0)

    def __str__(self):
        return f"{self.district_group} - {self.research} - {self.limit_count} - {self.type_period_limit}"

    class Meta:
        verbose_name = 'Участковая группа - ограничения назначений услуг'
        verbose_name_plural = 'Участковая группа - ограничения назначений услуг'

    @staticmethod
    def save_limit_assign(district_pk, data):
        with transaction.atomic():
            DistrictResearchLimitAssign.objects.filter(district_group_id=district_pk).delete()
            for t_b in data:
                type_period = 0 if t_b['type'] == 'День' else 1
                d = DistrictResearchLimitAssign(district_group_id=district_pk, research_id=t_b['current_researches'], limit_count=t_b['count'], type_period_limit=type_period)
                d.save()
