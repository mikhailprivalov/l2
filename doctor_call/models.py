import datetime
import os
import uuid
from typing import Optional

import simplejson as json
from django.db import models

import slog.models as slog
from appconf.manager import SettingManager
from clients.models import Card, District
from directory.models import Researches
from hospitals.models import Hospitals
from laboratory.utils import current_time, strfdatetime
from users.models import DoctorProfile


class DoctorCall(models.Model):
    PURPOSES = (
        (1, 'Больничный лист продление'),
        (2, 'Вызов врача-Неотложная помощь'),
        (3, 'Обострение хронического заболевания'),
        (4, 'Активное наблюдение'),
        (5, 'Другое'),
        (6, 'Лекарственное обеспечение'),
        (7, 'Заявка на отправку результата COVID-19'),
        (8, 'Скорая помощь'),
        (9, 'Вакцинация'),
        (10, 'Covid-19'),
        (11, 'Запись к врачу'),
        (12, 'Запись на обследования и анализы'),
        (13, 'Вызов волонтёров'),
        (14, 'Медицинская помощь-вопросы'),
        (15, 'ВМП-вопросы'),
        (16, 'Санаторно-курортное лечение'),
        (17, 'Доступность и качество'),
        (18, 'Нарушение прав граждан'),
        (19, 'Как обжаловать действий ЛПУ'),
        (20, 'Лицензирование'),
        (21, 'Кадровые вопросы'),
        (22, 'Льготы инвалидности, социальные'),
        (23, 'Справочные вопросы'),
        (24, 'Внешняя заявка'),
    )

    STATUS = (
        (1, 'Новая заявка'),
        (2, 'В работе'),
        (3, 'Выполнено'),
        (4, 'Отмена'),
    )

    client = models.ForeignKey(Card, db_index=True, help_text='Пациент', on_delete=models.CASCADE)
    research = models.ForeignKey(Researches, null=True, blank=True, help_text='Вид исследования из справочника', on_delete=models.CASCADE)
    create_at = models.DateTimeField(auto_now_add=True, help_text='Дата создания')
    exec_at = models.DateTimeField(help_text='Дата вызова на дом', db_index=True)
    comment = models.TextField()
    cancel = models.BooleanField(default=False, blank=True, help_text='Отмена вызова')
    doc_who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, help_text='Создатель вызова на дом', on_delete=models.SET_NULL)
    district = models.ForeignKey(District, default=None, null=True, blank=True, db_index=True, help_text="Участок", on_delete=models.SET_NULL)
    address = models.CharField(max_length=128, blank=True, default='', help_text="Адрес")
    phone = models.CharField(max_length=20, blank=True, default='', db_index=True)
    purpose = models.IntegerField(default=5, blank=True, db_index=True, choices=PURPOSES, help_text="Цель вызова")
    doc_assigned = models.ForeignKey(DoctorProfile, db_index=True, null=True, related_name="doc_assigned", help_text='Лечащий врач', on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospitals, db_index=True, null=True, help_text='Больница', on_delete=models.CASCADE)
    is_external = models.BooleanField(default=False, blank=True, help_text='Внешняя заявка')
    is_main_external = models.BooleanField(default=False, blank=True, help_text='Центральная заявка')
    need_send_status = models.BooleanField(default=False, blank=True, help_text='Требуется синхронизировать статус с центральной системой')
    need_send_to_external = models.BooleanField(default=False, blank=True, help_text='Требуется отправить в удалённую систему')
    external_num = models.CharField(max_length=128, blank=True, default='', help_text='Номер внешней заявки')
    email = models.CharField(max_length=64, blank=True, default=None, null=True, help_text='Email заявки на результат covid')
    executor = models.ForeignKey(DoctorProfile, db_index=True, null=True, related_name="executor", help_text='Исполнитель заявки', on_delete=models.CASCADE)
    status = models.PositiveSmallIntegerField(choices=STATUS, db_index=True, default=STATUS[0][0], blank=True)
    direction = models.ForeignKey(
        'directions.Napravleniya', db_index=True, blank=True, null=True, related_name="doc_call_direction", help_text='Связанное направление', on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = 'Вызов'
        verbose_name_plural = 'Вызова на дом'

    def get_status_data(self):
        return {
            "status": self.status,
            "executor": self.executor_id,
            "executor_fio": self.executor.get_fio() if self.executor else None,
            "inLog": DoctorCallLog.objects.filter(call=self).count(),
        }

    def json(self, doc: Optional[DoctorProfile] = None):
        return {
            "pk": self.pk,
            "num": self.num,
            "card": self.client.number_with_type_and_fio(),
            "cardPk": self.client_id,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "purpose": self.get_purpose_display(),
            "purpose_id": self.purpose,
            "comment": self.comment,
            "research": self.research.get_title(),
            "district": self.district.title if self.district else "",
            "hospital": self.hospital.safe_short_title if self.hospital else "",
            "docAssigned": self.doc_assigned.get_fio() if self.doc_assigned else "",
            "execAt": strfdatetime(self.exec_at, "%d.%m.%Y"),
            "isCancel": self.cancel,
            "isExternal": self.is_external,
            "isMainExternal": self.is_main_external,
            "needSendToExternal": self.need_send_to_external,
            "externalNum": self.external_num,
            "createdAt": strfdatetime(self.create_at, "%d.%m.%Y"),
            "createdAtTime": strfdatetime(self.create_at, "%X"),
            "status": self.status,
            "executor": self.executor_id,
            "executor_fio": self.executor.get_fio() if self.executor else None,
            "canEdit": (
                not self.need_send_to_external and (not doc or doc.all_hospitals_users_control or not self.hospital or self.hospital == doc.get_hospital()) and not self.is_main_external
            ),
            "inLog": DoctorCallLog.objects.filter(call=self).count(),
            "directionPk": self.direction_id,
        }

    @property
    def num(self):
        if self.is_main_external:
            return f"XR{self.pk}"
        return str(self.pk)

    @staticmethod
    def doctor_call_save(data, doc_who_create=None):
        patient_card = Card.objects.get(pk=data['card_pk']) if 'card' not in data else data['card']
        research_obj = Researches.objects.get(pk=data['research'])
        if int(data['district']) < 0:
            district_obj = None
        else:
            district_obj = District.objects.get(pk=data['district'])

        if int(data['doc']) < 0:
            doc_obj = None
        else:
            doc_obj = DoctorProfile.objects.get(pk=data['doc'])

        if int(data['purpose']) < 0:
            purpose = 5
        else:
            purpose = int(data['purpose'])

        hospital_obj: Optional[Hospitals]

        if int(data['hospital']) < 0:
            hospital_obj = None
        else:
            hospital_obj = Hospitals.objects.get(pk=data['hospital'])

        email = data.get('email')

        has_external_org = bool(hospital_obj and hospital_obj.remote_url)

        is_main_external = has_external_org and data.get('is_main_external', SettingManager.l2('send_doc_calls'))

        doc_call = DoctorCall(
            client=patient_card,
            research=research_obj,
            exec_at=datetime.datetime.strptime(data['date'], '%Y-%m-%d') if isinstance(data['date'], str) else data['date'],
            comment=data['comment'],
            doc_who_create=doc_who_create,
            cancel=False,
            district=district_obj,
            address=data['address'],
            phone=data['phone'],
            purpose=purpose,
            doc_assigned=doc_obj,
            hospital=hospital_obj,
            is_external=data['external'],
            is_main_external=bool(is_main_external),
            external_num=data.get('external_num') or '',
            email=None if not email else email[:64],
            need_send_to_external=has_external_org and SettingManager.l2('send_doc_calls') and not is_main_external,
            direction_id=data.get('direction'),
        )
        if data.get('as_executed'):
            doc_call.status = 3
            doc_call.executor = doc_who_create
        doc_call.save()

        slog.Log(
            key=doc_call.pk,
            type=80003,
            body=json.dumps(
                {
                    "card_pk": patient_card.pk,
                    "card": str(patient_card),
                    "research": research_obj.title,
                    "district": district_obj.title if district_obj else None,
                    "purpose": doc_call.get_purpose_display(),
                    "doc_assigned": str(doc_obj),
                    "hospital": str(hospital_obj),
                    "date": str(data['date']),
                    "comment": data['comment'],
                    "is_external": data['external'],
                    "external_num": data.get('external_num'),
                    "is_main_external": data.get('is_main_external'),
                    "email": email,
                    "as_executed": data.get('as_executed'),
                }
            ),
            user=doc_who_create,
        ).save()
        return doc_call

    @staticmethod
    def doctor_call_cancel(data, doc_who_create):
        doc_call = DoctorCall.objects.filter(pk=data['pk_doc_call'])[0]
        doc_call.doc_who_create = doc_who_create
        doc_call.cancel = not doc_call.cancel
        doc_call.save()

        slog.Log(
            key=doc_call.pk,
            type=80004,
            body=json.dumps({"card_pk": doc_call.client.pk, "status": doc_call.cancel}),
            user=doc_who_create,
        ).save()
        return doc_call.pk

    @staticmethod
    def doctor_call_get(data):
        if data.get('d1', None):
            d1 = datetime.datetime.strptime(data.get('d1'), '%d.%m.%Y')
        else:
            d1 = current_time()
        if data.get('d2', None):
            d2 = datetime.datetime.strptime(data.get('d2'), '%d.%m.%Y')
        else:
            d2 = current_time()

        start_date = datetime.datetime.combine(d1, datetime.time.min)
        end_date = datetime.datetime.combine(d2, datetime.time.max)
        if data.get('district', None):
            district_obj = District.objects.filter(pk__in=data.get('district'))
            result = DoctorCall.objects.filter(district__in=district_obj, exec_at__range=(start_date, end_date)).order_by("district")
        elif data.get('patient_pk', None):
            result = DoctorCall.objects.filter(client__pk=data.get('patient_pk')).order_by("exec_at")
        else:
            result = DoctorCall.objects.filter(exec_at__range=(start_date, end_date)).order_by("exec_at, district")

        return result


def get_file_path(instance: 'DoctorCallLog', filename):
    return os.path.join('doc_call_uploads', str(instance.call.pk), str(uuid.uuid4()), filename)


class DoctorCallLog(models.Model):
    call = models.ForeignKey(DoctorCall, db_index=True, on_delete=models.CASCADE)
    author = models.ForeignKey(DoctorProfile, related_name="doc_call_log_author", help_text='Автор записи', on_delete=models.CASCADE)
    text = models.TextField(blank=True, default='')
    status_update_from = models.PositiveSmallIntegerField(choices=DoctorCall.STATUS, null=True, blank=True, default=None)
    status_update_to = models.PositiveSmallIntegerField(choices=DoctorCall.STATUS, null=True, blank=True, default=None)
    executor_update_from = models.ForeignKey(DoctorProfile, related_name="doc_call_executor_update_from", on_delete=models.SET_NULL, null=True, blank=True, default=None)
    executor_update_to = models.ForeignKey(DoctorProfile, related_name="doc_call_executor_update_to", on_delete=models.SET_NULL, null=True, blank=True, default=None)
    uploaded_file = models.FileField(upload_to=get_file_path, blank=True, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
