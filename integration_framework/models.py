import psycopg2
from django.db.models import Q
from django.utils import timezone

from clients.models import Individual, Phones
from directions.models import Napravleniya
import uuid

from django.db import models

from directory.models import Researches
from equipment.models import Equipment
from hospitals.models import Hospitals
from laboratory.settings import DATABASES, SQL_QUERY_FOR_SELECT_DICOM_EQUIPMENT
from laboratory.utils import strdate
from slog.models import Log
from users.models import DoctorProfile
from utils.models import ChoiceArrayField
import simplejson as json
from django.core.cache import cache
from utils.db import namedtuplefetchall


class IntegrationNamespace(models.Model):
    key = models.CharField(max_length=128, primary_key=True)
    active = models.BooleanField()


class IntegrationJournal(models.Model):
    TYPE_DIRECTION = 0
    TYPE_RESULT = 1
    TYPES = ((TYPE_DIRECTION, 'DIRECTION'), (TYPE_RESULT, 'RESULT'))

    STATUS_NONE = 0
    STATUS_PENDING = 1
    STATUS_UPLOADED = 2
    STATUSES = ((STATUS_NONE, 'NONE'), (STATUS_PENDING, 'PENDING'), (STATUS_UPLOADED, 'UPLOADED'))

    namespace = models.ForeignKey(IntegrationNamespace, db_index=True, on_delete=models.CASCADE)
    type = models.SmallIntegerField(choices=TYPES, db_index=True)
    key = models.IntegerField(db_index=True)


class IntegrationResearches(models.Model):
    TYPES = (
        ('mbu', 'MBU'),
        ('amd', 'AMD'),
        ('crie', 'CRIE'),
        ('L2L2', 'L2L2'),
    )

    type_integration = models.CharField(max_length=4, choices=TYPES, db_index=True)
    research = models.ForeignKey(Researches, on_delete=models.CASCADE)


class TempData(models.Model):
    key = models.CharField(max_length=50, default="", blank=True, help_text='Приложение/объект', db_index=True)
    holter_protocol_date = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Последний обработанный протокол')


class ExternalServiceRights(models.Model):
    title = models.CharField(max_length=300, default="", blank=True, help_text='Название права', db_index=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Роли для внешнего сервиса'
        verbose_name_plural = 'Роли для внешних сервисы'


class ExternalService(models.Model):
    ACCESS_RIGHT_QR_CHECK_RESULT = 'qr_check_result'

    ACCESS_RIGHTS = ((ACCESS_RIGHT_QR_CHECK_RESULT, 'QR check result'),)

    title = models.CharField(max_length=127, help_text="Название")
    token = models.UUIDField(default=uuid.uuid4, editable=False, help_text="Токен, генерируется автоматически", db_index=True)
    rights = ChoiceArrayField(models.CharField(max_length=16, choices=ACCESS_RIGHTS), help_text='Права доступа')
    is_active = models.BooleanField(default=True, help_text="Сервис активен")
    extension_right = models.CharField(max_length=300, default="", blank=True, null=True, help_text="Название роли")
    external_service_rights = models.ForeignKey(ExternalServiceRights, default=None, null=True, blank=True, help_text='роль в базе', on_delete=models.SET_NULL)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Внешний сервис'
        verbose_name_plural = 'Внешние сервисы'


class CrieOrder(models.Model):
    local_direction = models.ForeignKey(Napravleniya, db_index=True, on_delete=models.CASCADE)
    system_id = models.IntegerField(db_index=True, null=True, blank=True)
    status = models.CharField(max_length=12, blank=True, default='null', db_index=True)
    error = models.TextField(blank=True, default='')


class IndividualAuth(models.Model):
    token = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    device_os = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_superuser = False
    is_authenticated = True
    is_confirmed = models.BooleanField(default=False, db_index=True, blank=True)
    confirmation_code = models.CharField(max_length=4, default=None, null=True, blank=True, db_index=True)
    confirmation_message_id = models.CharField(max_length=64, default=None, null=True, blank=True)
    code_check_count = models.IntegerField(default=0, db_index=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True, db_index=True)
    used_phone = models.CharField(max_length=64, default=None, null=True, blank=True, db_index=True)
    fcm_token = models.CharField(max_length=255, default=None, null=True, blank=True, db_index=True)

    @property
    def individuals(self):
        normalized_phones = Phones.normalize_to_search(self.used_phone)

        return (
            Individual.objects.filter(Q(owner__isnull=True) | Q(owner=Hospitals.get_default_hospital()))
            .filter(
                Q(card__phones__normalized_number__in=normalized_phones)
                | Q(card__phones__number__in=normalized_phones)
                | Q(card__phone__in=normalized_phones)
                | Q(card__doctorcall__phone__in=normalized_phones)
            )
            .distinct()
        )

    def __str__(self):
        return f"{self.used_phone} {self.device_os} {self.created_at:%Y-%m-%d %H:%M:%S}"


class IPLimitter(models.Model):
    ip = models.CharField(max_length=64, db_index=True)
    count = models.IntegerField(default=0, db_index=True)
    last_request = models.DateTimeField(auto_now=True, db_index=True)

    @staticmethod
    def get_ip(ip):
        if not ip:
            return None
        try:
            return IPLimitter.objects.get(ip=ip)
        except IPLimitter.DoesNotExist:
            return None

    @staticmethod
    def add_ip(ip):
        if not ip:
            return None
        try:
            ip_obj = IPLimitter.objects.get(ip=ip)
            if (timezone.now() - ip_obj.last_request).seconds < 60 * 60:
                ip_obj.count += 1
            else:
                ip_obj.count = 1
            ip_obj.last_request = timezone.now()
            ip_obj.save()
        except IPLimitter.DoesNotExist:
            ip_obj = IPLimitter.objects.create(ip=ip, count=1)
        return ip_obj

    @staticmethod
    def clear_ip(ip):
        if not ip:
            return None
        try:
            IPLimitter.objects.filter(ip=ip).delete()
        except IPLimitter.DoesNotExist:
            pass
        return None

    @staticmethod
    def is_limit(ip):
        if not ip:
            return False
        ip_obj = IPLimitter.get_ip(ip)
        if not ip_obj:
            return False
        if ip_obj.count >= 100 and (timezone.now() - ip_obj.last_request).seconds < 60 * 10:
            return True
        if ip_obj.count >= 20 and (timezone.now() - ip_obj.last_request).seconds < 60:
            return True
        if (timezone.now() - ip_obj.last_request).seconds < 5:
            return True
        return False

    @staticmethod
    def check_limit(ip):
        IPLimitter.add_ip(ip)
        return not IPLimitter.is_limit(ip)


class EquipmentReceive(models.Model):
    napravleniye = models.ForeignKey(Napravleniya, blank=True, null=True, default=None, help_text='Направление', db_index=True, on_delete=models.CASCADE, related_name='equipment_receive')
    family = models.CharField(max_length=120, default=None, null=True, blank=True, help_text="Фамилия", db_index=True)
    name = models.CharField(max_length=120, default=None, null=True, blank=True, help_text="Имя", db_index=True)
    patronymic = models.CharField(max_length=120, default=None, null=True, blank=True, help_text="Отчество", db_index=True)
    birthday = models.DateField(help_text="Дата рождения", default=None, null=True, blank=True, db_index=True)
    sex = models.CharField(max_length=2, default="м", help_text="Пол", db_index=True)
    order_id = models.CharField(max_length=64, default=None, null=True, blank=True, db_index=True, help_text="ID в результате")
    doc_save_link = models.ForeignKey(
        DoctorProfile, null=True, blank=True, default=None, related_name="doc_save_link", db_index=True, help_text='Пользователь связавший снимок с заказом', on_delete=models.SET_NULL
    )
    time_save_link = models.DateTimeField(null=True, blank=True, default=None, db_index=True, help_text='Время создания связи')
    doc_reset_link = models.ForeignKey(
        DoctorProfile, null=True, blank=True, default=None, related_name="doc_reset_link", db_index=True, help_text='Пользователь анулировавший связь', on_delete=models.SET_NULL
    )
    time_reset_link = models.DateTimeField(null=True, blank=True, default=None, db_index=True, help_text='Время анулирвоания свзязи')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, help_text='Время создания записи')
    updated_at = models.DateTimeField(auto_now=True, help_text='Время последнего изменения записи')
    tag_patient_name = models.CharField(max_length=255, blank=True, null=True, default=None, help_text="ТЭГ - ФИО пациента")
    tag_study_date = models.CharField(max_length=10, blank=True, null=True, default=None, help_text="ТЭГ - study date")
    tag_station_name = models.CharField(max_length=255, blank=True, null=True, default=None, help_text="ТЭГ - название станции")
    tag_institution_name = models.CharField(max_length=255, blank=True, null=True, default=None, help_text="ТЭГ - название организации")
    tag_manufacturer = models.CharField(max_length=64, default=None, null=True, blank=True, db_index=True, help_text="tag 0008,0070")
    tag_manufacturer_model_name = models.CharField(max_length=64, default=None, null=True, blank=True, db_index=True, help_text="tag 0008,1090")
    tag_device_serial_number = models.CharField(max_length=64, default=None, null=True, blank=True, db_index=True, help_text="tag 0018,1000")
    tag_patient_sex = models.CharField(max_length=1, blank=True, null=True, default=None, help_text="ТЭГ - пол")
    tag_patient_birthdate = models.CharField(max_length=10, blank=True, null=True, default=None, help_text="ТЭГ - дата рождения")
    tag_patient_id = models.CharField(max_length=64, default=None, null=True, blank=True, db_index=True, help_text="Patient ID")
    tag_sex = models.CharField(max_length=64, default=None, null=True, blank=True, db_index=True, help_text="tag Пол")
    study_instance_uid_tag = models.CharField(max_length=64, blank=True, null=True, default=None, help_text="study instance_uid tag", db_index=True)
    tag_instance_id = models.CharField(max_length=64, blank=True, null=True, default=None, help_text="study instance_id", db_index=True)
    equipment_title = models.CharField(max_length=64, blank=True, null=True, default=None, db_index=True, help_text="ТЭГ - оборудование, разделен 8 точками")
    equipment_model = models.ForeignKey(Equipment, blank=True, null=True, default=None, db_index=True, on_delete=models.CASCADE)
    ip_address = models.CharField(max_length=40, blank=True, null=True, default=None, db_index=True, help_text="ТЭГ - ip - адрес")

    def __str__(self):
        patient_name = f"{self.family} {self.name} {self.patronymic}".strip()
        if not patient_name:
            patient_name = "Без имени"
        status = "Связано" if self.doc_save_link else "Не связано"
        date_str = strdate(self.created_at) if self.created_at else ""
        uid_short = self.study_instance_uid_tag[:20] + "..." if self.study_instance_uid_tag and len(self.study_instance_uid_tag) > 20 else self.study_instance_uid_tag or "Без UID"
        naprav_info = f"№{self.napravleniye.pk}" if self.napravleniye else "Без направления"
        patient_id_info = f" (ID:{self.tag_patient_id})" if self.tag_patient_id else ""
        return f"[{status}] {patient_name}{patient_id_info} - {naprav_info} - {uid_short} - {date_str}"

    @staticmethod
    def get_equipment_receive(manufacturer_param='', manufacturer_model_name_param='', institution_name_param='', ip_address_param='', station_name_param=''):
        id_equipment_receive = None
        database = DATABASES.get("default")["NAME"]
        user = DATABASES.get("default")["USER"]
        password = DATABASES.get("default")["PASSWORD"]
        address = DATABASES.get("default")["HOST"]
        port = DATABASES.get("default")["PORT"]
        connection = psycopg2.connect(database=database, user=user, password=password, host=address, port=port)
        cursor = connection.cursor()
        for query in SQL_QUERY_FOR_SELECT_DICOM_EQUIPMENT:
            query.replace('manufacturer_param', manufacturer_param).\
                replace('manufacturer_model_name_param', manufacturer_model_name_param).\
                replace('institution_name_param', institution_name_param).\
                replace('ip_address_param', ip_address_param).replace('station_name_param', station_name_param)

            cursor.execute(query)
            rows = namedtuplefetchall(cursor)
            if len(rows) > 0:
                id_equipment_receive = rows[0].id
                break

        cursor.close()
        connection.close()
        return id_equipment_receive

    @staticmethod
    def save_meta_tag_from_dicom_server(request):
        data = json.loads(request.body)
        cache_key = f"dcm:study_instance_uid:{data.get('study_instance_uid_tag')}"
        study_instance_uid_tag = cache.get(cache_key)
        eqr = None
        if not study_instance_uid_tag:
            Log(
                key=f"{data.get('tag_patient_name')}",
                type=6001,
                body=data,
                user=None,
            ).save()
            tag_manufacturer = data.get("tag_manufacturer")
            tag_manufacturer_model_name = data.get("tag_manufacturer_model_name")
            tag_institution_name = data.get("tag_institution_name")
            tag_station_name = data.get("tag_station_name")
            tag_sender_ip = data.get("tag_sender_ip")
            equipment_model = Equipment.objects.filter(
                Q(manufacturer=tag_manufacturer) & Q(station_name=tag_station_name) & (Q(institution_name=tag_institution_name) | Q(manufacturer_model_name=tag_manufacturer_model_name))
            ).first()

            pk_equipment_receive = EquipmentReceive.get_equipment_receive(
                manufacturer_param=tag_manufacturer,
                manufacturer_model_name_param=tag_manufacturer_model_name,
                institution_name_param=tag_institution_name,
                ip_address_param=tag_sender_ip,
                station_name_param=tag_station_name
            )
            # equipment_model = Equipment.objects.filter(pk=pk_equipment_receive)
            if equipment_model:
                eqr = EquipmentReceive(
                    tag_patient_name=data.get("tag_patient_name"),
                    tag_study_date=data.get("tag_study_date"),
                    tag_station_name=data.get("tag_station_name"),
                    tag_institution_name=data.get("tag_institution_name"),
                    tag_manufacturer=tag_manufacturer,
                    tag_manufacturer_model_name=tag_manufacturer_model_name,
                    tag_patient_sex=data.get("tag_patient_sex"),
                    tag_patient_birthdate=data.get("tag_patient_birthdate"),
                    tag_instance_id=data.get("tag_instanceId"),
                    tag_patient_id=data.get("tag_patient_id"),
                    tag_device_serial_number=data.get("tag_device_serial_number"),
                    tag_sex=data.get("tag_sex"),
                    study_instance_uid_tag=data.get("study_instance_uid_tag"),
                    equipment_model=equipment_model,
                    equipment_title=equipment_model.title,
                    ip_address=tag_sender_ip,
                ).save()
                cache.set(cache_key, data.get('study_instance_uid_tag'), 60 * 60 * 24)
        return eqr
