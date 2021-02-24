import re
import time
import unicodedata
from datetime import date
from typing import Optional

import simplejson as json
from django.contrib.auth.models import User
from django.db import models, transaction
from django.utils import timezone
from jsonfield import JSONField
import clients.models as Clients
import directory.models as directory
import slog.models as slog
import users.models as umodels
import cases.models as cases
from api.models import Application
from hospitals.models import Hospitals
from laboratory.utils import strdate, localtime, current_time
from refprocessor.processor import RefProcessor
from users.models import DoctorProfile
import contracts.models as contracts
from statistics_tickets.models import VisitPurpose, ResultOfTreatment, Outcomes, Place

from appconf.manager import SettingManager


class FrequencyOfUseResearches(models.Model):
    research = models.ForeignKey(directory.Researches, on_delete=models.CASCADE)
    user = models.ForeignKey(DoctorProfile, db_index=True, on_delete=models.CASCADE)
    cnt = models.IntegerField(default=0)

    def __str__(self):
        return str(self.user) + " - " + str(self.research) + ", " + str(self.cnt)

    @staticmethod
    def inc(research, user):
        if not FrequencyOfUseResearches.objects.filter(research=research, user=user).exists():
            FrequencyOfUseResearches(research=research, user=user, cnt=0).save()

        f = FrequencyOfUseResearches.objects.filter(research=research, user=user)[0]
        f.cnt += 1
        f.save()

    @staticmethod
    def reset(user):
        for f in FrequencyOfUseResearches.objects.filter(user=user):
            f.cnt = 0
            f.save()

    class Meta:
        verbose_name = 'Частота назначения исследований пользователем'
        verbose_name_plural = 'Частоты назначения исследований пользователем'


class CustomResearchOrdering(models.Model):
    research = models.ForeignKey(directory.Researches, on_delete=models.CASCADE)
    user = models.ForeignKey(DoctorProfile, db_index=True, on_delete=models.CASCADE)
    weight = models.IntegerField(default=0)

    def __str__(self):
        return str(self.user) + " - " + str(self.research) + ", " + str(self.weight)

    class Meta:
        verbose_name = 'Пользовательская сортировка исследований'
        verbose_name_plural = 'Пользовательские сортировки исследований'


class TubesRegistration(models.Model):
    """
    Таблица с пробирками для исследований
    """

    id = models.AutoField(primary_key=True, db_index=True)
    type = models.ForeignKey(directory.ReleationsFT, help_text='Тип ёмкости', on_delete=models.CASCADE)
    time_get = models.DateTimeField(null=True, blank=True, help_text='Время взятия материала', db_index=True)
    doc_get = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True, related_name='docget', help_text='Кто взял материал', on_delete=models.SET_NULL)
    time_recive = models.DateTimeField(null=True, blank=True, help_text='Время получения материала', db_index=True)
    doc_recive = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True, related_name='docrecive', help_text='Кто получил материал', on_delete=models.SET_NULL)
    barcode = models.CharField(max_length=255, null=True, blank=True, help_text='Штрих-код или номер ёмкости', db_index=True)
    notice = models.CharField(max_length=512, default="", blank=True, help_text='Замечания', db_index=True)
    daynum = models.IntegerField(default=0, blank=True, null=True, help_text='Номер принятия ёмкости среди дня в лаборатории')

    @property
    def time_get_local(self):
        return localtime(self.time_get)

    @property
    def time_recive_local(self):
        return localtime(self.time_recive)

    def __str__(self):
        return "%d %s (%s, %s) %s" % (self.pk, self.type.tube.title, self.doc_get, self.doc_recive, self.notice)

    def day_num(self, doc, num):
        if not self.getstatus():
            iss = Issledovaniya.objects.filter(tubes=self)
            if iss.count():
                self.set_get(iss[0].napravleniye.doc)
        new_t = False
        if not self.rstatus():
            new_t = True
            self.set_r(doc)
        if not self.daynum:
            self.daynum = num
            self.save()

        return {"n": self.daynum, "new": new_t}

    def set_get(self, doc_get):
        """
        Установка статуса взятия
        :param doc_get: врач/мед сестра, взявшая материал
        :return: None
        """
        from django.utils import timezone

        self.time_get = timezone.now()
        self.doc_get = doc_get
        self.barcode = self.pk
        self.save()
        slog.Log(key=str(self.pk), type=9, body="", user=doc_get).save()

    def getstatus(self, one_by_one=False):
        """
        Получение статуса взятия
        :return:
        """
        return (self.time_get_local is not None and self.doc_get is not None) or (self.type.receive_in_lab and one_by_one)

    def set_r(self, doc_r):
        """
        Установка статуса принятия материала лабораторией
        :param doc_r: врач/лаборант, принявший материал
        :return:
        """
        from django.utils import timezone

        if not self.getstatus():
            self.set_get(doc_r)

        self.time_recive = timezone.now()
        self.doc_recive = doc_r
        self.save()
        slog.Log(key=str(self.pk), user=doc_r, type=11, body=json.dumps({"Замечание не приёма": self.notice}) if self.notice != "" else "").save()

    def set_notice(self, doc_r, notice):
        """
        Установка замечания для пробирки
        :param doc_r: врач/лаборант, указавший замечание
        :param notice: текст замечания
        :return:
        """
        notice = notice.strip()
        if notice != "":
            self.doc_recive = None
            self.time_recive = None
        self.notice = notice
        self.save()
        slog.Log(key=str(self.pk), user=doc_r, type=12, body=json.dumps({"Замечание не приёма": self.notice})).save()

    def clear_notice(self, doc_r):
        old_notice = self.notice
        if old_notice == "":
            return
        self.notice = ""
        self.save()
        slog.Log(key=str(self.pk), user=doc_r, type=4000, body=json.dumps({"Удалённое замечание": old_notice})).save()

    def rstatus(self, check_not=False):
        """
        Получение статуса принятия материала лабораторией
        :return: статус принятия
        """
        if self.doc_recive and (not check_not or self.notice == ""):
            return True
        return False

    def getbc(self):
        """
        Получение номера штрих-кода
        :return: штрих-код
        """
        if self.barcode and self.barcode.isnumeric():
            return self.barcode
        return self.id

    class Meta:
        verbose_name = 'Ёмкость для направления'
        verbose_name_plural = 'Ёмкости для направлений'


class IstochnikiFinansirovaniya(models.Model):
    """
    Таблица источников финансирования
    """

    title = models.CharField(max_length=511, help_text='Название')
    active_status = models.BooleanField(default=True, help_text='Статус активности')
    base = models.ForeignKey(Clients.CardBase, help_text='База пациентов, к которой относится источник финансирования', db_index=True, on_delete=models.CASCADE)
    hide = models.BooleanField(default=False, blank=True, help_text="Скрытие", db_index=True)
    rmis_auto_send = models.BooleanField(default=True, blank=True, help_text="Автоматическая отправка в РМИС", db_index=True)
    default_diagnos = models.CharField(max_length=36, help_text="Диагноз по умолчанию", default="", blank=True)
    contracts = models.ForeignKey(contracts.Contract, null=True, blank=True, default='', on_delete=models.CASCADE)
    order_weight = models.SmallIntegerField(default=0)

    def __str__(self):
        return "{} {} (скрыт: {})".format(self.base, self.title, self.hide)

    @staticmethod
    def get_price_modifier(finsource, work_place_link=None):
        """
        На основании источника финансирования возвращает прайс(объект)+модификатор(множитель цены)
        Если источник финансирования ДМС поиск осуществляется по цепочке company-contract. Company(Страховая организация)
        Если источник финансирования МЕДОСМОТР поиск осуществляется по цепочке company-contract. Company(место работы)
        Если источник финансирования ПЛАТНО поиск осуществляется по цепочке ист.фин-contract-прайс
        Если источник финансирования ОМС, ДИСПАНСЕРИЗАЦИЯ поиск осуществляется по цепочке ист.фин-contract-прайс
        Если источник финансирования Бюджет поиск осуществляется по цепочке contract
        """
        price_modifier = None
        price_contract = set(SettingManager.get("price_contract").split(','))
        price_company = set(SettingManager.get("price_company").split(','))
        if finsource:
            if finsource.title.upper() in price_contract:
                contract_l = IstochnikiFinansirovaniya.objects.values_list('contracts_id').filter(pk=finsource.pk).first()
                if contract_l[0]:
                    price_modifier = contracts.Contract.objects.values_list('price', 'modifier').get(id=contract_l[0])
            elif finsource.title.upper() in price_company and work_place_link:
                contract_l = work_place_link.contract_id
                if contract_l:
                    price_modifier = contracts.Contract.objects.values_list('price', 'modifier').get(id=contract_l)

        return price_modifier

    class Meta:
        verbose_name = 'Источник финансирования'
        verbose_name_plural = 'Источники финансирования'


class Diagnoses(models.Model):
    M = (
        (0, "Диапазон"),
        (1, "Группа"),
        (2, "Значение"),
    )
    code = models.CharField(max_length=255, db_index=True)
    title = models.TextField(db_index=True)
    parent = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    d_type = models.CharField(max_length=255, db_index=True)
    m_type = models.IntegerField(choices=M, db_index=True)
    rmis_id = models.CharField(max_length=128, db_index=True, blank=True, default=None, null=True)

    def __str__(self):
        return "{} {}".format(self.code, self.title)


class KeyValue(models.Model):
    key = models.CharField(max_length=255, db_index=True)
    value = models.TextField(db_index=True)

    def __str__(self):
        return "{} {}".format(self.key, self.value)


class RMISServiceInactive(models.Model):
    rmis_id = models.CharField(max_length=30, primary_key=True)
    enabled = models.BooleanField(default=True, blank=True)

    @staticmethod
    def checkInactive(serviceId, enabled):
        r = RMISServiceInactive.objects.filter(rmis_id=serviceId)
        if not r.exists() and enabled:
            RMISServiceInactive(rmis_id=serviceId, enabled=enabled).save()
        elif r.exists() and r[0].enabled != enabled:
            r[0].enabled = enabled
            r[0].save()

    @staticmethod
    def isInactive(serviceId):
        r = RMISServiceInactive.objects.filter(rmis_id=serviceId)
        return r.exists() and r[0].enabled

    def __str__(self):
        return "{} {}".format(self.rmis_id, self.enabled)


class RMISOrgs(models.Model):
    rmis_id = models.IntegerField(primary_key=True, editable=False)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class ExternalOrganization(models.Model):
    title = models.CharField(max_length=255)
    hide = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Внешняя организация'
        verbose_name_plural = 'Внешние организации'


class Napravleniya(models.Model):
    """
    Таблица направлений
    """

    PURPOSE_PRELIMINARY_EXAMINATION = 'PRELIMINARY_EXAMINATION'
    PURPOSE_WORK_EXAMINATION = 'WORK_EXAMINATION'
    PURPOSE_DRIVE_EXAMINATION = 'DRIVE_EXAMINATION'
    PURPOSE_WEAPON_EXAMINATION = 'WEAPON_EXAMINATION'
    PURPOSE_PERIODIC_EXAMINATION = 'PERIODIC_EXAMINATION'
    PURPOSE_CONSULTATION = 'CONSULTATION'
    PURPOSE_SIMPLE_EXAMINATION = 'SIMPLE_EXAMINATION'
    PURPOSE_HOSPITALIZATION = 'OSPITALIZATION'

    PURPOSES = (
        (PURPOSE_PRELIMINARY_EXAMINATION, 'Предварительный медосмотр'),
        (PURPOSE_WORK_EXAMINATION, 'На работу'),
        (PURPOSE_DRIVE_EXAMINATION, 'На водительское'),
        (PURPOSE_WEAPON_EXAMINATION, 'На оружие'),
        (PURPOSE_PERIODIC_EXAMINATION, 'Периодический медосмотр'),
        (PURPOSE_CONSULTATION, 'Консультация'),
        (PURPOSE_SIMPLE_EXAMINATION, 'Обследование'),
        (PURPOSE_HOSPITALIZATION, 'Госпитализация'),
    )

    data_sozdaniya = models.DateTimeField(auto_now_add=True, help_text='Дата создания направления', db_index=True)
    visit_date = models.DateTimeField(help_text='Дата посещения по направлению', db_index=True, default=None, blank=True, null=True)
    visit_who_mark = models.ForeignKey(
        DoctorProfile, related_name="visit_who_mark", default=None, blank=True, null=True, help_text='Профиль, который отметил посещение', on_delete=models.SET_NULL
    )
    diagnos = models.CharField(max_length=511, help_text='Диагноз', default='', blank=True)
    vich_code = models.CharField(max_length=12, help_text='Код для направления на СПИД', default='', blank=True)
    client = models.ForeignKey(Clients.Card, db_index=True, help_text='Пациент', on_delete=models.CASCADE)
    doc = models.ForeignKey(DoctorProfile, db_index=True, null=True, help_text='Лечащий врач', on_delete=models.CASCADE)
    istochnik_f = models.ForeignKey(IstochnikiFinansirovaniya, blank=True, null=True, help_text='Источник финансирования', on_delete=models.CASCADE)
    history_num = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='Номер истории')
    additional_num = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='Дополнительный номер')
    microbiology_num = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='Микробиология номер')
    rmis_case_id = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='РМИС: Номер случая')
    rmis_visit_id = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='РМИС: Номер посещения')
    rmis_hosp_id = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='РМИС: ЗОГ')
    rmis_resend_services = models.BooleanField(default=False, blank=True, help_text='Переотправить услуги?', db_index=True)
    doc_who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_who_create", help_text='Создатель направления', on_delete=models.SET_NULL)
    cancel = models.BooleanField(default=False, blank=True, help_text='Отмена направления')
    rmis_number = models.CharField(max_length=15, default=None, blank=True, null=True, db_index=True, help_text='ID направления в РМИС')
    result_rmis_send = models.BooleanField(default=False, blank=True, help_text='Результат отправлен в РМИС?', db_index=True)
    imported_from_rmis = models.BooleanField(default=False, blank=True, db_index=True, help_text='Направление создано на основе направления из РМИС?')
    imported_org = models.ForeignKey(RMISOrgs, default=None, blank=True, null=True, on_delete=models.SET_NULL)
    imported_directions_rmis_send = models.BooleanField(default=False, blank=True, help_text='Для направления из РМИС отправлен бланк', db_index=True)
    force_rmis_send = models.BooleanField(default=False, blank=True, help_text='Подтверждение ручной отправки в РМИС')
    forcer_rmis_send = models.ForeignKey(
        DoctorProfile, default=None, blank=True, null=True, related_name="doc_forcer_rmis_send", help_text='Исполнитель подтверждения отправки в РМИС', on_delete=models.SET_NULL
    )

    case = models.ForeignKey(cases.Case, default=None, blank=True, null=True, help_text='Случай обслуживания', on_delete=models.SET_NULL)
    num_contract = models.CharField(max_length=25, default=None, blank=True, null=True, db_index=True, help_text='Номер контракта')
    protect_code = models.CharField(max_length=32, default=None, blank=True, null=True, db_index=True, help_text="Контрольная сумма контракта")

    polis_who_give = models.TextField(blank=True, null=True, default=None, help_text="Страховая компания")
    polis_n = models.CharField(max_length=62, blank=True, null=True, default=None, help_text="Полис")
    parent = models.ForeignKey('Issledovaniya', related_name='parent_iss', help_text="Протокол-основание", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    parent_auto_gen = models.ForeignKey(
        'Issledovaniya', related_name='parent_auto_gen', help_text="Авто сгенерированное", db_index=True, blank=True, null=True, default=None, on_delete=models.SET_NULL
    )
    parent_slave_hosp = models.ForeignKey(
        'Issledovaniya', related_name='parent_slave_hosp', help_text="Из стационарного протокола", db_index=True, blank=True, null=True, default=None, on_delete=models.SET_NULL
    )
    rmis_slot_id = models.CharField(max_length=15, blank=True, null=True, default=None, help_text="РМИС слот")
    microbiology_n = models.CharField(max_length=10, blank=True, default='', help_text="Номер в микробиологической лаборатории")
    time_microbiology_receive = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Дата/время приёма материала микробиологии')
    doc_microbiology_receive = models.ForeignKey(
        DoctorProfile, default=None, blank=True, null=True, related_name="doc_microbiology_receive", help_text='Кто принял материал микробиологии', on_delete=models.SET_NULL
    )
    need_resend_amd = models.BooleanField(default=False, blank=True, help_text='Требуется отправка в АМД?')
    need_resend_n3 = models.BooleanField(default=False, blank=True, help_text='Требуется отправка в N3?')
    need_resend_l2 = models.BooleanField(default=False, blank=True, help_text='Требуется отправка в L2.Core?')
    core_id = models.CharField(max_length=32, default=None, blank=True, null=True, db_index=True, help_text='Номер документа в L2.Core')
    amd_number = models.CharField(max_length=15, default=None, blank=True, null=True, db_index=True, help_text='Номер документа в АМД')
    error_amd = models.BooleanField(default=False, blank=True, help_text='Ошибка отправка в АМД?')
    amd_excluded = models.BooleanField(default=False, blank=True, help_text='Исключить из выгрузки в АМД?')
    purpose = models.CharField(max_length=64, null=True, blank=True, default=None, db_index=True, choices=PURPOSES, help_text="Цель направления")
    external_organization = models.ForeignKey(ExternalOrganization, default=None, blank=True, null=True, help_text='Внешняя организация', on_delete=models.SET_NULL)
    harmful_factor = models.CharField(max_length=255, blank=True, default='')
    workplace = models.CharField(max_length=255, blank=True, default='', db_index=True)
    hospital = models.ForeignKey(Hospitals, default=None, blank=True, null=True, on_delete=models.SET_NULL)
    id_in_hospital = models.CharField(max_length=15, default=None, blank=True, null=True, db_index=True, help_text='Номер документа во внешней организации')
    is_external = models.BooleanField(default=False, blank=True, null=True)
    rmis_case_number = models.CharField(max_length=15, default=None, blank=True, null=True, db_index=True, help_text='ID случая в РМИС')
    rmis_visit_number = models.CharField(max_length=15, default=None, blank=True, null=True, db_index=True, help_text='ID посещения в РМИС')

    def get_doc_podrazdeleniye_title(self):
        if self.hospital and (self.is_external or not self.hospital.is_default):
            parts = [
                self.hospital_short_title,
            ]
        else:
            parts = []

        if self.doc and self.doc.podrazdeleniye:
            parts.append(self.doc.podrazdeleniye.title)

        return ', '.join(parts)

    def get_hospital(self):
        if self.doc and self.doc.hospital and not self.is_external:
            if self.hospital != self.doc.hospital:
                self.hospital = self.doc.hospital
                self.save(update_fields=['hospital'])
            return self.doc.hospital
        if not self.hospital:
            self.hospital = Hospitals.get_default_hospital()
            self.save(update_fields=['hospital'])
        return self.hospital

    @property
    def hospital_title(self):
        hosp = self.get_hospital()
        if hosp:
            return hosp.title
        return SettingManager.get("org_title")

    @property
    def hospital_short_title(self):
        hosp = self.get_hospital()
        if hosp:
            return hosp.safe_short_title
        return SettingManager.get("org_title")

    @property
    def hospital_address(self):
        hosp = self.get_hospital()
        if hosp:
            return hosp.safe_address
        return SettingManager.get("org_address")

    @property
    def hospital_phones(self):
        hosp = self.get_hospital()
        if hosp:
            return hosp.safe_phones
        return SettingManager.get("org_phones")

    @property
    def hospital_www(self):
        hosp = self.get_hospital()
        if hosp:
            return hosp.safe_www
        return SettingManager.get("org_www")

    @property
    def data_sozdaniya_local(self):
        return localtime(self.data_sozdaniya)

    @property
    def visit_date_local(self):
        return localtime(self.visit_date)

    def __str__(self):
        return "%d для пациента %s (врач %s, выписал %s, %s, %s, %s, par: [%s])" % (
            self.pk,
            self.client.individual.fio(),
            "" if not self.doc else self.doc.get_fio(),
            self.doc_who_create,
            self.rmis_number,
            self.rmis_case_id,
            self.rmis_hosp_id,
            str(self.parent),
        )

    def get_instructions(self):
        r = []
        for i in Issledovaniya.objects.filter(napravleniye=self).exclude(research__instructions=""):
            r.append({"pk": i.research_id, "title": i.research.title, "text": i.research.instructions})
        return r

    @property
    def fin_title(self):
        return self.istochnik_f.title if self.istochnik_f else ''

    def set_polis(self):
        i = self.client.get_data_individual(empty=True)
        c = False
        if i['oms']['polis_num']:
            n = ('' if not i['oms']['polis_serial'] else i['oms']['polis_serial'] + ' ') + i['oms']['polis_num']
            if n != self.polis_n:
                c = True
                self.polis_n = n
        if i['oms']['polis_issued'] and self.polis_who_give != i['oms']['polis_issued']:
            self.polis_who_give = i['oms']['polis_issued']
            c = True
        if c:
            self.save()

    @staticmethod
    def gen_napravleniye(
        client_id: int,
        doc: DoctorProfile,
        istochnik_f: IstochnikiFinansirovaniya,
        diagnos: str,
        historynum: str,
        doc_current: DoctorProfile,
        ofname_id: [int, None],
        ofname: DoctorProfile,
        issledovaniya: [list, None] = None,
        save: bool = True,
        for_rmis: bool = False,
        rmis_data: [dict, None] = None,
        parent_id=None,
        parent_auto_gen_id=None,
        parent_slave_hosp_id=None,
        rmis_slot=None,
        direction_purpose="NONE",
        external_organization="NONE",
    ) -> 'Napravleniya':
        """
        Генерация направления
        :param client_id:
        :param doc:
        :param istochnik_f:
        :param diagnos:
        :param historynum:
        :param doc_current:
        :param ofname_id:
        :param ofname:
        :param issledovaniya:
        :param save:
        :param for_rmis:
        :param rmis_data:
        :param parent_id:
        :param parent_auto_gen_id:
        :return: Созданное направление
        """
        if rmis_data is None:
            rmis_data = {}
        if issledovaniya is None:
            pass
        client = Clients.Card.objects.get(pk=client_id)
        dir = Napravleniya(
            client=client,
            doc=doc if not for_rmis else None,
            istochnik_f=istochnik_f,
            data_sozdaniya=timezone.now(),
            diagnos=diagnos,
            cancel=False,
            parent_id=parent_id,
            parent_auto_gen_id=parent_auto_gen_id,
            parent_slave_hosp_id=parent_slave_hosp_id,
            rmis_slot_id=rmis_slot,
            hospital=doc.hospital or Hospitals.get_default_hospital(),
        )
        dir.additional_num = client.number_poliklinika
        dir.harmful_factor = dir.client.harmful_factor
        dir.workplace = client.work_place_db.title if client.work_place_db else client.work_place
        if for_rmis:
            dir.rmis_number = rmis_data.get("rmis_number")
            dir.imported_from_rmis = True
            dir.imported_org = RMISOrgs.objects.filter(rmis_id=rmis_data.get("imported_org", -1)).first()
            dir.doc = None
            dir.doc_who_create = doc_current
        else:
            if historynum != "":
                dir.history_num = historynum
            if ofname_id > -1 and ofname:
                dir.doc = ofname
                dir.doc_who_create = doc_current
        if direction_purpose != "NONE":
            dir.purpose = direction_purpose
        if external_organization != "NONE":
            dir.external_organization_id = int(external_organization)
        if save:
            dir.save()
        dir.set_polis()
        return dir

    @staticmethod
    def set_of_name(dir: 'Napravleniya', doc_current: DoctorProfile, ofname_id: int, ofname: DoctorProfile):
        """
        Проверка на выписывание направления от имени другого врача и установка этого имени в направление, если необходимо
        :rtype: Null
        :param dir: направление
        :param doc_current: текущий врач, выписавший направление
        :param ofname_id: id врача, от которого выписывается направление
        :param ofname: объект с профилем врача, от которого выписывается направление
        :return: Null
        """
        if ofname_id > -1 and ofname:
            dir.doc = ofname
            dir.doc_who_create = doc_current
            dir.save()

    @staticmethod
    def gen_napravleniya_by_issledovaniya(
        client_id,
        diagnos,
        finsource,
        history_num,
        ofname_id,
        doc_current,
        researches,
        comments,
        for_rmis=None,
        rmis_data=None,
        vich_code='',
        count=1,
        discount=0,
        parent_iss=None,
        parent_slave_hosp=None,
        rmis_slot=None,
        counts=None,
        localizations=None,
        service_locations=None,
        visited=None,
        parent_auto_gen=None,
        direction_purpose="NONE",
        external_organization="NONE",
    ):
        if not visited:
            visited = []
        if counts is None:
            counts = {}

        if localizations is None:
            localizations = {}

        if service_locations is None:
            service_locations = {}

        if rmis_data is None:
            rmis_data = {}

        childrens = {}
        researches_grouped_by_lab = []  # Лист с выбранными исследованиями по лабораториям
        i = 0
        result = {"r": False, "list_id": []}
        ofname_id = ofname_id or -1
        ofname = None
        if not Clients.Card.objects.filter(pk=client_id).exists():
            result["message"] = "Карта в базе не зарегистрирована, попробуйте выполнить поиск заново"
            return result
        card = Clients.Card.objects.get(pk=client_id)

        if finsource and isinstance(finsource, str) and not finsource.isdigit():
            f_obj: Optional[IstochnikiFinansirovaniya] = (
                IstochnikiFinansirovaniya.objects.filter(base=card.base, title="ОМС", hide=False).first()
                or IstochnikiFinansirovaniya.objects.filter(base=card.base, hide=False).order_by('-order_weight').first()
            )
            if not f_obj:
                finsource = None
            else:
                finsource = f_obj.pk

        if client_id and researches:  # если client_id получен и исследования получены
            if ofname_id > -1:
                ofname = umodels.DoctorProfile.objects.get(pk=ofname_id)

            no_attach = False
            conflict_list = []
            conflict_keys = []
            for v in researches:  # нормализация исследований
                researches_grouped_by_lab.append({v: researches[v]})

                for vv in researches[v]:
                    research_tmp = directory.Researches.objects.get(pk=vv)
                    if research_tmp.no_attach and research_tmp.no_attach > 0:
                        if research_tmp.no_attach not in conflict_keys:
                            conflict_keys.append(research_tmp.no_attach)
                            if not no_attach:
                                conflict_list = [research_tmp.title]
                        else:
                            no_attach = True
                            conflict_list.append(research_tmp.title)
                i += 1

            res = []
            for v in researches_grouped_by_lab:  # цикл перевода листа в словарь
                for key in v.keys():
                    res += v[key]
                    # {5:[0,2,5,7],6:[8]}

            if not no_attach:
                directions_for_researches = {}  # Словарь для временной записи направлений.
                # Исследования привязываются к направлению по группе

                finsource = IstochnikiFinansirovaniya.objects.filter(pk=finsource).first()

                # получить прайс
                work_place_link = card.work_place_db
                price_obj = IstochnikiFinansirovaniya.get_price_modifier(finsource, work_place_link)

                for v in res:
                    research = directory.Researches.objects.get(pk=v)
                    research_coast = None

                    # пользователю добавлять данные услуги в направления(не будут добавлены)
                    if research in doc_current.restricted_to_direct.all():
                        continue

                    dir_group = -1
                    if research.direction:
                        dir_group = research.direction_id

                    if dir_group > -1 and dir_group not in directions_for_researches.keys():
                        directions_for_researches[dir_group] = Napravleniya.gen_napravleniye(
                            client_id,
                            doc_current if not for_rmis else None,
                            finsource,
                            diagnos,
                            history_num,
                            doc_current,
                            ofname_id,
                            ofname,
                            for_rmis=for_rmis,
                            rmis_data=rmis_data,
                            parent_id=parent_iss,
                            parent_auto_gen_id=parent_auto_gen,
                            parent_slave_hosp_id=parent_slave_hosp,
                            rmis_slot=rmis_slot,
                            direction_purpose=direction_purpose,
                            external_organization=external_organization,
                        )

                        result["list_id"].append(directions_for_researches[dir_group].pk)
                    if dir_group == -1:
                        dir_group = "id" + str(research.pk)
                        directions_for_researches[dir_group] = Napravleniya.gen_napravleniye(
                            client_id,
                            doc_current if not for_rmis else None,
                            finsource,
                            diagnos,
                            history_num,
                            doc_current,
                            ofname_id,
                            ofname,
                            for_rmis=for_rmis,
                            rmis_data=rmis_data,
                            parent_id=parent_iss,
                            parent_auto_gen_id=parent_auto_gen,
                            parent_slave_hosp_id=parent_slave_hosp,
                            rmis_slot=rmis_slot,
                            direction_purpose=direction_purpose,
                            external_organization=external_organization,
                        )

                        result["list_id"].append(directions_for_researches[dir_group].pk)

                    # получить по прайсу и услуге: текущую цену
                    research_coast = contracts.PriceCoast.get_coast_from_price(research.pk, price_obj)

                    discount_end = discount
                    if research.prior_discount:
                        discount_end = research.def_discount

                    research_discount = discount_end * -1
                    research_howmany = int(counts.get(str(research.pk), 1))

                    if research_howmany == 1:
                        research_howmany = count

                    issledovaniye = Issledovaniya(
                        napravleniye=directions_for_researches[dir_group], research=research, coast=research_coast, discount=research_discount, how_many=research_howmany, deferred=False
                    )
                    loc = ""
                    if str(research.pk) in localizations:
                        localization = directory.Localization.objects.get(pk=localizations[str(research.pk)]["code"])
                        issledovaniye.localization = localization
                        loc = localization.barcode
                    if str(research.pk) in service_locations and service_locations[str(research.pk)]:
                        s = directory.ServiceLocation.objects.get(pk=service_locations[str(research.pk)]["code"])
                        issledovaniye.service_location = s
                    issledovaniye.comment = loc or (comments.get(str(research.pk), "") or "")[:40]
                    issledovaniye.save()
                    if issledovaniye.pk not in childrens:
                        childrens[issledovaniye.pk] = {}

                    for raa in research.auto_add_hidden.all():
                        if raa.pk in visited:
                            continue
                        visited.append(raa.pk)
                        if raa.reversed_type not in childrens[issledovaniye.pk]:
                            childrens[issledovaniye.pk][raa.reversed_type] = []
                        childrens[issledovaniye.pk][raa.reversed_type].append(raa.pk)

                    FrequencyOfUseResearches.inc(research, doc_current)
                for k, v in directions_for_researches.items():
                    if Issledovaniya.objects.filter(napravleniye=v, research__need_vich_code=True).exists():
                        v.vich_code = vich_code
                        v.save()
                result["r"] = True
                slog.Log(
                    key=json.dumps(result["list_id"]),
                    user=doc_current,
                    type=21,
                    body=json.dumps(
                        {
                            "researches": researches,
                            "client_num": card.number,
                            "client_id": client_id,
                            "diagnos": diagnos,
                            "finsource": "" if not finsource else finsource.title + " " + finsource.base.title,
                            "history_num": history_num,
                            "ofname": str(ofname),
                            "for_rmis": for_rmis,
                            "rmis_data": rmis_data,
                            "comments": comments,
                            "count": count,
                            "discount": discount,
                        }
                    ),
                ).save()

            else:
                result["r"] = False
                result["message"] = "Следующие исследования не могут быть назначены вместе: " + ", ".join(conflict_list)
        for iss_parent_pk in childrens:
            if not childrens[iss_parent_pk]:
                continue
            res_children = Napravleniya.gen_napravleniya_by_issledovaniya(
                client_id,
                diagnos,
                finsource.pk,
                history_num,
                ofname_id,
                doc_current,
                childrens[iss_parent_pk],
                comments,
                for_rmis,
                rmis_data,
                vich_code,
                count,
                discount,
                iss_parent_pk,
                rmis_slot,
                counts,
                localizations,
                service_locations,
                visited=visited,
            )
            if not res_children["r"]:
                return res_children
            result['list_id'].extend(res_children['list_id'])
        return result

    def has_confirm(self):
        """
        Есть ли подтверждение у одного или более исследований в направлении
        :return: True, если есть подтверждение у одного или более
        """
        return any([x.time_confirmation is not None for x in Issledovaniya.objects.filter(napravleniye=self)])

    def is_all_confirm(self):
        """
        Есть ли подтверждение у всех исследований в направлении
        :return: True, если всё подтверждено
        """
        return all([x.time_confirmation is not None for x in Issledovaniya.objects.filter(napravleniye=self)])

    def is_has_deff(self):
        """
        Есть ли отложенные исследования
        :return: True, если подтверждены не все и есть одно или более отложенное исследование
        """
        return not self.is_all_confirm() and any([x.deferred for x in Issledovaniya.objects.filter(napravleniye=self)])

    def department(self):
        if Issledovaniya.objects.filter(napravleniye=self).exists():
            return Issledovaniya.objects.filter(napravleniye=self)[0].research.podrazdeleniye
        return None

    def rmis_direction_type(self) -> str:
        dep = self.department()
        if dep:
            return dep.rmis_direction_type
        from rmis_integration.client import Settings

        return Settings.get("direction_type_title", default="Направление в лабораторию")

    def rmis_department_title(self) -> str:
        if self.is_external:
            return "КДЛ"
        dep = self.department()
        if dep:
            return dep.rmis_department_title
        from rmis_integration.client import Settings

        return Settings.get("depname")

    def rmis_referral_title(self) -> str:
        if self.is_external:
            return "КДЛ"
        return self.doc.podrazdeleniye.rmis_department_title

    def get_attr(self):
        """
        Получает на входе объект Направление
        возвращает словарь атрибутов направлению
        :return:
        """
        napr_data = {}
        ind_data = self.client.get_data_individual()
        napr_data['client_fio'] = ind_data['fio']
        napr_data['client_bd'] = ind_data['born']
        napr_data['card_num'] = ind_data['card_num']
        napr_data['number_poliklinika'] = ind_data['number_poliklinika']
        napr_data['polis_n'] = self.polis_n if self.polis_n else ''
        napr_data['polis_who_give'] = self.polis_who_give if self.polis_who_give else ''
        napr_data['istochnik_f'] = self.fin_title.lower()

        return napr_data

    @property
    def amd_status(self):
        if self.is_all_confirm():
            has_amd = SettingManager.l2_modules().get("l2_amd", False)

            if has_amd:
                if self.need_resend_amd:
                    return "planned"
                elif self.amd_excluded:
                    return "excluded"
                if self.error_amd:
                    return "error"
                elif self.amd_number:
                    return "ok"
                else:
                    return "need"
        return "not_need"

    class Meta:
        verbose_name = 'Направление'
        verbose_name_plural = 'Направления'


class PersonContract(models.Model):
    """
    Каждый раз при генерации нового контракта для физлица создается просто запись
    """

    num_contract = models.CharField(max_length=25, null=False, db_index=True, help_text='Номер договора')
    protect_code = models.CharField(max_length=32, null=False, db_index=True, help_text="Контрольная сумма контракта")
    dir_list = models.CharField(max_length=512, null=False, db_index=True, help_text="Направления для контракта")
    sum_contract = models.CharField(max_length=255, null=False, db_index=True, help_text="Итоговая сумма контракта")
    patient_data = models.CharField(max_length=255, null=False, db_index=True, help_text="Фамилия инициалы Заказчика-Пациента")
    patient_card = models.ForeignKey(Clients.Card, related_name='patient_card', null=True, help_text='Карта пациента', db_index=True, on_delete=models.SET_NULL)
    payer_card = models.ForeignKey(Clients.Card, related_name='payer_card', null=True, help_text='Карта плательщика', db_index=False, on_delete=models.SET_NULL)
    agent_card = models.ForeignKey(Clients.Card, related_name='agent_card', null=True, help_text='Карта Представителя', db_index=False, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ("num_contract", "protect_code")
        verbose_name = 'Договор физ.лица'
        verbose_name_plural = 'Договоры физ.лиц'

    @staticmethod
    def person_contract_save(n_contract, p_code, d_list, s_contract, p_data, p_card, p_payer=None, p_agent=None):
        """
        Запись в базу сведений о контракте
        """
        pers_contract = PersonContract(
            num_contract=n_contract, protect_code=p_code, dir_list=d_list, sum_contract=s_contract, patient_data=p_data, patient_card=p_card, payer_card=p_payer, agent_card=p_agent
        )
        pers_contract.save()


class Issledovaniya(models.Model):
    """
    Направления на исследования
    """

    napravleniye = models.ForeignKey(Napravleniya, null=True, help_text='Направление', db_index=True, on_delete=models.CASCADE)
    research = models.ForeignKey(directory.Researches, null=True, blank=True, help_text='Вид исследования из справочника', db_index=True, on_delete=models.CASCADE)
    tubes = models.ManyToManyField(TubesRegistration, help_text='Ёмкости, необходимые для исследования', db_index=True)
    doc_save = models.ForeignKey(
        DoctorProfile, null=True, blank=True, related_name="doc_save", db_index=True, help_text='Профиль пользователя, сохранившего результат', on_delete=models.SET_NULL
    )
    time_save = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время сохранения результата')
    doc_confirmation = models.ForeignKey(
        DoctorProfile, null=True, blank=True, related_name="doc_confirmation", db_index=True, help_text='Профиль пользователя, подтвердившего результат', on_delete=models.SET_NULL
    )
    doc_confirmation_string = models.CharField(max_length=64, null=True, blank=True, default=None)
    time_confirmation = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время подтверждения результата')
    deferred = models.BooleanField(default=False, blank=True, help_text='Флаг, отложено ли иследование', db_index=True)
    comment = models.CharField(max_length=255, default="", blank=True, help_text='Комментарий (отображается на ёмкости)')
    lab_comment = models.TextField(default="", null=True, blank=True, help_text='Комментарий, оставленный лабораторией')
    api_app = models.ForeignKey(Application, null=True, blank=True, default=None, help_text='Приложение API, через которое результаты были сохранены', on_delete=models.SET_NULL)
    coast = models.DecimalField(max_digits=10, null=True, blank=True, default=None, decimal_places=2)
    discount = models.SmallIntegerField(default=0, help_text='Скидка назначена оператором')
    how_many = models.PositiveSmallIntegerField(default=1, help_text='Кол-во услуг назначено оператором')
    def_uet = models.DecimalField(max_digits=6, null=True, help_text="Нагрузка врача(лаборанта) подтвердившего результат", blank=True, default=None, decimal_places=3)
    co_executor = models.ForeignKey(DoctorProfile, related_name="co_executor", help_text="Со-исполнитель", default=None, null=True, blank=True, on_delete=models.SET_NULL)
    co_executor_uet = models.DecimalField(max_digits=6, null=True, blank=True, default=None, decimal_places=3)
    co_executor2 = models.ForeignKey(DoctorProfile, related_name="co_executor2", help_text="Со-исполнитель2", default=None, null=True, blank=True, on_delete=models.SET_NULL)
    co_executor2_uet = models.DecimalField(max_digits=6, null=True, blank=True, default=None, decimal_places=3)
    purpose = models.ForeignKey(VisitPurpose, default=None, blank=True, null=True, on_delete=models.SET_NULL, help_text="Цель посещения")
    fin_source = models.ForeignKey(IstochnikiFinansirovaniya, default=None, blank=True, null=True, on_delete=models.SET_NULL, help_text="Перезаписать источник финансирования из направления")
    first_time = models.BooleanField(default=False, help_text="Впервые")
    result_reception = models.ForeignKey(ResultOfTreatment, default=None, blank=True, null=True, on_delete=models.SET_NULL, help_text="Результат обращения")
    outcome_illness = models.ForeignKey(Outcomes, default=None, blank=True, null=True, on_delete=models.SET_NULL, help_text="Исход")
    place = models.ForeignKey(Place, default=None, blank=True, null=True, on_delete=models.SET_NULL, help_text="Условие оказание помощи")
    diagnos = models.CharField(blank=True, help_text="Заключительный Диагноз приема", default="", max_length=255)
    maybe_onco = models.BooleanField(default=False, help_text="Подозрение на онко")
    creator = models.ForeignKey(
        DoctorProfile,
        null=True,
        blank=True,
        default=None,
        related_name="doc_add_research",
        db_index=True,
        help_text='Профиль пользователя, добавившего услуги к созданному направлению',
        on_delete=models.SET_NULL,
    )
    parent = models.ForeignKey('self', related_name='parent_issledovaniye', help_text="Исследование основание", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    medical_examination = models.DateField(blank=True, null=True, default=None, help_text="Дата осмотра")
    localization = models.ForeignKey(directory.Localization, blank=True, null=True, default=None, help_text="Локализация", on_delete=models.SET_NULL)
    service_location = models.ForeignKey(directory.ServiceLocation, blank=True, null=True, default=None, help_text="Место оказания услуги", on_delete=models.SET_NULL)
    link_file = models.CharField(max_length=255, blank=True, null=True, default=None, help_text="Ссылка на файл")
    study_instance_uid = models.CharField(max_length=55, blank=True, null=True, default=None, help_text="uuid снимка")
    gen_direction_with_research_after_confirm = models.ForeignKey(
        directory.Researches, related_name='research_after_confirm', null=True, blank=True, help_text='Авто назначаемое при подтверждении', on_delete=models.SET_NULL
    )
    aggregate_lab = JSONField(null=True, blank=True, default=None, help_text='ID направлений лаборатории, привязаных к стационарному случаю')
    aggregate_desc = JSONField(null=True, blank=True, default=None, help_text='ID направлений описательных, привязаных к стационарному случаю')
    microbiology_conclusion = models.TextField(default=None, null=True, blank=True, help_text='Заключение по микробиологии')

    @property
    def time_save_local(self):
        return localtime(self.time_save)

    @property
    def time_confirmation_local(self):
        return localtime(self.time_confirmation)

    def get_stat_diagnosis(self):
        pass

    @property
    def doc_confirmation_fio(self):
        if self.doc_confirmation_string:
            return self.doc_confirmation_string
        if self.doc_confirmation:
            return self.doc_confirmation.get_fio()
        return ''

    def gen_after_confirm(self, user: User):
        if not self.time_confirmation or not self.gen_direction_with_research_after_confirm:
            return
        Napravleniya.gen_napravleniya_by_issledovaniya(
            self.napravleniye.client_id,
            "",
            self.napravleniye.parent.napravleniye.istochnik_f_id if self.napravleniye.parent else self.napravleniye.istochnik_f_id,
            "",
            None,
            user.doctorprofile,
            {-1: [self.gen_direction_with_research_after_confirm_id]},
            {},
            False,
            {},
            vich_code="",
            count=1,
            discount=0,
            parent_iss=self.napravleniye.parent_id or self.pk,
            parent_auto_gen=None,
        )

    def __str__(self):
        return "%s %s" % (str(self.napravleniye), self.research.title)

    def is_get_material(self):
        """
        Осуществлен ли забор всего материала для исследования
        :return: True, если весь материал взят
        """
        return self.tubes.filter().exists() and all([x.doc_get is not None for x in self.tubes.filter()])

    def get_visit_date(self, force=False):
        if not self.time_confirmation and not force:
            return ""
        if not self.napravleniye.visit_date or not self.napravleniye.visit_who_mark:
            self.napravleniye.visit_date = timezone.now()
            self.napravleniye.visit_who_mark = self.doc_confirmation
            self.napravleniye.save()
        return strdate(self.napravleniye.visit_date)

    def get_medical_examination(self):
        if not self.medical_examination:
            if self.napravleniye.visit_date or self.time_confirmation:
                self.medical_examination = (self.napravleniye.visit_date or self.time_confirmation).date()
            else:
                self.medical_examination = current_time(only_date=True)
            self.save(update_fields=['medical_examination'])
        return self.medical_examination

    def is_receive_material(self):
        """
        Осуществлен ли прием материала лабораторией
        :return: True, если весь материал принят
        """
        return self.is_get_material() and all([x.doc_recive is not None for x in self.tubes.filter()])

    def get_analyzer(self):
        return "" if not self.api_app else self.api_app.name

    def allow_reset_confirm(self, user: User):
        from api.stationar.stationar_func import forbidden_edit_dir

        if not self.time_confirmation:
            return False
        if user.is_superuser:
            return True
        groups = [str(x) for x in user.groups.all()]
        if self.research.can_transfer:
            return "Сброс подтверждения переводного эпикриза" in groups
        if self.research.is_extract:
            return "Сброс подтверждения выписки" in groups
        if forbidden_edit_dir(self.napravleniye_id):
            return False
        ctp = int(0 if not self.time_confirmation else int(time.mktime(timezone.localtime(self.time_confirmation).timetuple())))
        ctime = int(time.time())
        current_doc_confirmation = self.doc_confirmation
        rt = SettingManager.get("lab_reset_confirm_time_min") * 60
        return (ctime - ctp < rt and current_doc_confirmation == user.doctorprofile) or "Сброс подтверждений результатов" in groups

    class Meta:
        verbose_name = 'Назначение на исследование'
        verbose_name_plural = 'Назначения на исследования'


class MethodsOfTaking(models.Model):
    drug_prescription = models.CharField(max_length=128, db_index=True)
    method_of_taking = models.CharField(max_length=128, db_index=True)
    count = models.IntegerField()

    @staticmethod
    def inc(dp, method):
        objs = MethodsOfTaking.objects.filter(drug_prescription=dp, method_of_taking=method)
        if not objs.exists():
            MethodsOfTaking(drug_prescription=dp, method_of_taking=method, count=1).save()
        else:
            obj = objs[0]
            obj.count += 1
            obj.save()

    @staticmethod
    def dec(dp, method):
        objs = MethodsOfTaking.objects.filter(drug_prescription=dp, method_of_taking=method)
        if objs.exists():
            obj = objs[0]
            obj.count -= 1
            obj.save()


class Recipe(models.Model):
    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True, help_text='Направление на исследование, для которого сохранен рецепт', on_delete=models.CASCADE)
    drug_prescription = models.CharField(max_length=128, db_index=True)
    method_of_taking = models.CharField(max_length=128)
    comment = models.CharField(max_length=128)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class TypeJob(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    hide = models.BooleanField(help_text="Скрыть тип", default=False)
    value = models.DecimalField(max_digits=5, decimal_places=2, help_text="Ценность работы (в УЕТ или минутах-зависит от названия работы)")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Тип работы'
        verbose_name_plural = 'Типы работ'


class EmployeeJob(models.Model):
    type_job = models.ForeignKey(TypeJob, db_index=True, help_text='Тип косвенных работ', on_delete=models.CASCADE)
    count = models.SmallIntegerField(default=0, help_text="Количество данного типа", blank=True)
    doc_execute = models.ForeignKey(
        DoctorProfile, null=True, blank=True, related_name="doc_execute", db_index=True, help_text='Профиль пользователя, выполневший работы', on_delete=models.SET_NULL
    )
    date_job = models.DateField(default=date.today, help_text="Дата работ", blank=True, null=True, db_index=True)
    time_save = models.DateTimeField(default=timezone.now, null=True, blank=True, help_text='Время сохранения/корректировки')
    canceled_at = models.DateTimeField(default=None, null=True, blank=True, help_text='Время отмены')
    who_do_cancel = models.ForeignKey(
        DoctorProfile, null=True, blank=True, related_name="who_do_cancel", db_index=True, help_text='Профиль пользователя, выполневший отмену', on_delete=models.SET_NULL
    )

    @property
    def time_save_local(self):
        return localtime(self.time_save)

    class Meta:
        verbose_name = 'Нагрузка сотрудника'
        verbose_name_plural = 'Учет нагрзки'


class ParaclinicResult(models.Model):
    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True, help_text='Направление на исследование, для которого сохранен результат', on_delete=models.CASCADE)
    field = models.ForeignKey(directory.ParaclinicInputField, db_index=True, help_text='Поле результата', on_delete=models.CASCADE)
    field_type = models.SmallIntegerField(default=None, blank=True, choices=directory.ParaclinicInputField.TYPES, null=True)
    value = models.TextField()

    def get_field_type(self):
        return self.field_type if self.issledovaniye.time_confirmation and self.field_type is not None else self.field.field_type

    @staticmethod
    def anesthesia_value_get(iss_pk=-1, field_pk=-1):
        if iss_pk > 0:
            paraclinic_result_obj = ParaclinicResult.objects.filter(issledovaniye__pk=iss_pk, field__pk=field_pk).first()
            if paraclinic_result_obj:
                return paraclinic_result_obj.value
        else:
            return ""

    @staticmethod
    def anesthesia_value_save(iss_pk=-1, field_pk=-1, value_anesthesia=None, action='add'):
        if value_anesthesia is None:
            value_anesthesia = {}
        previus_result = ParaclinicResult.anesthesia_value_get(iss_pk, field_pk)
        if previus_result:
            previus_result = eval(previus_result)
        else:
            previus_result = {'patient_params': [], 'potent_drugs': [], 'narcotic_drugs': [], 'times': []}

        if not isinstance(previus_result, dict):
            previus_result = {'patient_params': [], 'potent_drugs': [], 'narcotic_drugs': [], 'times': []}

        temp_times = previus_result['times']
        current_time = value_anesthesia.get('time')
        if current_time not in temp_times and action == 'add':
            temp_times.append(current_time)
        elif action == 'del':
            temp_times.remove(current_time)
        temp_times = sorted(temp_times)
        previus_result['times'] = temp_times

        def made_anesthesia_structure(type):
            for k, v in value_anesthesia.get(type).items():
                if action == 'add':
                    if k not in previus_result[type]:
                        previus_result[type].append(k)
                    if previus_result.get(k):
                        temp_attr = previus_result[k]
                        temp_attr[current_time] = v
                        previus_result[k] = temp_attr
                    else:
                        previus_result[k] = {current_time: v}

                elif action == 'del':
                    if previus_result.get(k):
                        temp_attr = previus_result[k]
                        if current_time in temp_attr:
                            del temp_attr[current_time]
                            previus_result[k] = temp_attr

        made_anesthesia_structure('patient_params')
        made_anesthesia_structure('potent_drugs')
        made_anesthesia_structure('narcotic_drugs')

        paraclinic_result_obj = None
        if iss_pk > 0:
            iss_obj = Issledovaniya.objects.get(pk=iss_pk)
            field_obj = directory.ParaclinicInputField.objects.get(pk=field_pk)
            paraclinic_result_obj = ParaclinicResult.objects.filter(issledovaniye=iss_obj, field=field_obj).first()
            if paraclinic_result_obj:
                paraclinic_result_obj.value = previus_result
                paraclinic_result_obj.field_type = 21
            else:
                paraclinic_result_obj = ParaclinicResult(issledovaniye=iss_obj, field=field_obj, field_type=21, value=previus_result)
            paraclinic_result_obj.save()

        return paraclinic_result_obj


class MicrobiologyResultCulture(models.Model):
    issledovaniye = models.ForeignKey(
        Issledovaniya, db_index=True, help_text='Направление на исследование, для которого сохранен результат', on_delete=models.CASCADE, related_name='culture_results'
    )
    culture = models.ForeignKey(directory.Culture, help_text="Культура", on_delete=models.PROTECT)
    koe = models.CharField(max_length=16, help_text='КОЕ')
    comments = models.TextField(default='')

    class Meta:
        verbose_name = 'Результат-культура'
        verbose_name_plural = 'Результат-культуры'


class MicrobiologyResultCultureAntibiotic(models.Model):
    SENSITIVITIES = (
        ('S', 'S'),
        ('R', 'R'),
        ('I', 'I'),
    )

    result_culture = models.ForeignKey(MicrobiologyResultCulture, help_text="Результат-культура", on_delete=models.CASCADE, related_name='culture_antibiotic')
    antibiotic = models.ForeignKey(directory.Antibiotic, help_text="Антибиотик", on_delete=models.PROTECT)
    antibiotic_amount = models.CharField(max_length=30, help_text='Дозировка антибиотика', default='', blank=True)
    sensitivity = models.CharField(max_length=1, choices=SENSITIVITIES, help_text="Чувствительность")
    dia = models.CharField(max_length=64, help_text='Диаметр')

    class Meta:
        verbose_name = 'Результат-культура-антибиотик'
        verbose_name_plural = 'Результат-культура-антибиотики'


class RmisServices(models.Model):
    napravleniye = models.ForeignKey(Napravleniya, help_text='Направление', db_index=True, on_delete=models.CASCADE)
    code = models.TextField(help_text='Код выгруженной услуги', db_index=True)
    rmis_id = models.CharField(max_length=15, default="", blank=True, help_text='ID выгруженной услуги в РМИС')

    def __str__(self):
        return "%s %s" % (self.napravleniye, self.code)

    class Meta:
        verbose_name = 'Выгруженная в РМИС услуга для направления'
        verbose_name_plural = 'Выгруженные в РМИС услуги для направлений'


class Result(models.Model):
    """
    Результат исследований
    """

    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True, help_text='Направление на исследование, для которого сохранен результат', on_delete=models.CASCADE)
    fraction = models.ForeignKey(directory.Fractions, help_text='Фракция из исследования', db_index=True, on_delete=models.CASCADE)
    value = models.TextField(null=True, blank=True, help_text='Значение')
    iteration = models.IntegerField(default=1, null=True, help_text='Итерация')
    is_normal = models.CharField(max_length=255, default="", null=True, blank=True, help_text="Это норма?")
    ref_sign = models.CharField(max_length=3, default="", null=True, blank=True, help_text="Направление отклонения от нормы")
    ref_m = JSONField(default=None, blank=True, null=True, help_text="Референсы М")
    ref_f = JSONField(default=None, blank=True, null=True, help_text="Референсы Ж")
    units = models.CharField(max_length=255, default=None, blank=True, null=True, help_text="Единицы измерения")
    ref_title = models.CharField(max_length=255, default=None, blank=True, null=True, help_text="Референсы Название")
    ref_about = models.TextField(default=None, blank=True, null=True, help_text="Референсы Описание")

    def __str__(self):
        return "%s | %s | %s" % (self.pk, self.fraction, self.ref_m is not None and self.ref_f is not None)

    def get_units(self, needsave=True):
        if not self.units and self.fraction.units and self.fraction.units != "":
            self.units = self.fraction.units
            if needsave:
                self.save()
        return self.units or ""

    def get_ref(self, as_str=False, full=False, fromsave=False, re_save=False, needsave=True):
        if (not self.ref_title and not fromsave) or re_save:
            self.ref_title = "Default" if self.fraction.default_ref is None else self.fraction.default_ref.title
            self.save()
            if not self.ref_m or re_save:
                self.ref_m = self.fraction.ref_m if self.fraction.default_ref is None else self.fraction.default_ref.ref_m
                if needsave:
                    self.save()

            if not self.ref_f or re_save:
                self.ref_f = self.fraction.ref_f if self.fraction.default_ref is None else self.fraction.default_ref.ref_f
                if needsave:
                    self.save()

            if not self.ref_about or re_save:
                self.ref_about = "" if self.fraction.default_ref is None else self.fraction.default_ref.about
                if needsave:
                    self.save()

        if full:
            return {"title": self.ref_title, "about": self.ref_about, "m": self.ref_m, "f": self.ref_f}

        ref = self.ref_f if self.issledovaniye.napravleniye.client.individual.sex.lower() != "м" else self.ref_m

        if isinstance(ref, str):
            ref = json.loads(ref)
        if not ref:
            ref = {}

        if not as_str:
            return ref
        else:
            return json.dumps(ref)

    def save(self, *args, **kw):
        norm, ref_sign = self.calc_normal(True)
        self.is_normal = norm
        self.ref_sign = ref_sign
        super(Result, self).save(*args, **kw)

    def get_is_norm(self, recalc=False, with_ref=False):
        if self.is_normal == "" or recalc:
            norm, ref_sign = self.calc_normal()
            if self.is_normal != norm or self.ref_sign != ref_sign:
                self.is_normal = norm
                self.ref_sign = ref_sign
                self.save(update_fields=['is_normal', 'ref_sign'])
        else:
            norm = self.is_normal
            ref_sign = self.ref_sign
        if with_ref:
            return norm, ref_sign, self.calc_normal(only_ref=True, fromsave=True, raw_ref=True, single=True)
        return norm, ref_sign

    def calc_normal(self, fromsave=False, only_ref=False, raw_ref=True, single=False):
        value = self.value
        ref = self.get_ref(fromsave=fromsave)
        age = self.issledovaniye.napravleniye.client.individual.age(iss=self.issledovaniye, days_monthes_years=True)

        ref_processor = RefProcessor(ref, age)

        if only_ref:
            return ref_processor.get_active_ref(raw_ref=raw_ref, single=single)

        return ref_processor.calc(value)

    def get_is_norm_old(self, recalc=False):
        if self.is_normal == "" or recalc:
            norm = self.calc_normal_old()
            if self.is_normal != norm:
                self.save()
        else:
            norm = self.is_normal
        return norm

    def calc_normal_old(self, fromsave=False, only_ref=False, raw_ref=True):
        import operator
        from functools import reduce

        trues = {True: ["полож.", "положительно", "да", "положительный", "обнаружено"], False: ["отриц.", "отрицательно", "нет", "1/0", "отрицательный", "не обнаружено"]}
        signs = {">": [">", "&gt;", "более", "старше"], "<": ["<", "&lt;", "до", "младше", "менее"]}

        value = self.value
        days, monthes, years = self.issledovaniye.napravleniye.client.individual.age(iss=self.issledovaniye, days_monthes_years=True)

        ref = self.get_ref(fromsave=fromsave)

        def isnum(r):
            return r.replace(".", "", 1).replace(",", "", 1).isdigit()

        def replace_pow(v):
            v = str(v).replace(" ", "")
            for j in range(1, 9):
                for i in range(0, 12):
                    v = v.replace("%s*10<sup>%s</sup>" % (j, i), str(j * (10 ** i)))
            for i in range(0, 12):
                v = v.replace("10<sup>%s</sup>" % str(i), str(10 ** i))
            return v

        def val_normalize(v):
            if v == float("inf"):
                return v
            v = replace_pow(v)
            '''
            if any([x in v for x in signs["<"]]):
                pass
            elif any([x in v for x in signs[">"]]):
                pass'''

            import re

            tmp = re.findall("\d+,\d+", v)
            for t in tmp:
                v = v.replace(t, t.replace(",", "."))
            tmp = re.findall("\d+\.\d+", v)
            if len(tmp) == 0:
                tmp = re.findall('\d+', v)
                if len(tmp) == 0:
                    return False
            return tmp[-1]

        def rigths(r):
            if r == "все" or r == "":
                return 0, 200

            if "старше" in r.lower():
                r = r.replace("старше", "").strip()
                if r.isdigit():
                    return int(r), 200

            if "после" in r.lower():
                r = r.replace("после", "").strip()
                if r.isdigit():
                    return int(r), 200

            if "младше" in r.lower():
                r = r.replace("младше", "").strip()
                if r.isdigit():
                    return 0, int(r)

            if "до" in r.lower():
                r = r.replace("до", "").strip()
                if r.isdigit():
                    return 0, int(r)

            spl = r.split("-")
            if len(spl) == 2 and spl[0].isdigit() and spl[1].isdigit():
                return int(spl[0]), int(spl[1])
            return False

        def rigths_v(r):
            r = replace_pow(r.replace(" ", ""))
            if r == "":
                return -float("inf"), float("inf")
            if "един" in r.lower():
                r = "0-2"
            if "отсутств" in r.lower():
                r = "0-0"
            trues_vars = [x for x in trues.values()]
            trues_vars = reduce(operator.add, trues_vars)
            if any([x in r for x in trues_vars]):
                return r in trues[True]
            spl = r.split("-")
            if len(spl) == 2:
                x = spl[0]
                y = spl[1]
                if isnum(x) and isnum(y):
                    x = val_normalize(x)
                    y = val_normalize(y)
                    return float(x) - 0.00001, float(y) + 0.00001
            signs_vars = [x for x in signs.values()]
            signs_vars = reduce(operator.add, signs_vars)
            if any([x in r for x in signs_vars]):
                val_r = val_normalize(r)
                if not val_r:
                    val_r = "0.0"
                if any([x in r for x in signs["<"]]):
                    return -float("inf"), float(val_r) - 0.00001
                elif any([x in r for x in signs[">"]]):
                    return float(val_r) + 0.00001, float("inf")
            return r.lower().strip()

        def test_value(right, value):
            import re

            if isinstance(right, bool):
                return value.lower() in trues[right]
            if right == "":
                return True
            value = value.replace("''", "\"")
            if isinstance(right, tuple) and len(right) == 2:
                if isinstance(right[0], float) and isinstance(right[1], float):
                    if "един" in value.lower():
                        value = "1"
                    if "отсутств" in value.lower():
                        value = "0"
                    if "сплошь" in value.lower() or "++" in value or "+ +" in value or "++++" in value or "+" == value.strip() or "оксал ед" in value:
                        value = float("inf")
                    elif any([x in replace_pow(value) for x in signs["<"]]):
                        value = val_normalize(value)
                        if value and not isinstance(value, bool):
                            value = str(float(value) - 0.1)
                    elif any([x in replace_pow(value) for x in signs[">"]]):
                        value = val_normalize(value)
                        if value and not isinstance(value, bool):
                            value = str(float(value) + 0.1)
                    if isinstance(value, str) and re.match(r"(\d)\'(\d{1,2})\"", value.replace(" ", "")):
                        m = re.search(r"(\d)\'(\d{1,2})\"", value.replace(" ", ""))
                        min = int(m.group(1))
                        sec = int(m.group(2))
                        value = "{0:.2f}".format(min + sec / 60)
                    else:
                        value = val_normalize(value)
                    if not isinstance(right, bool):
                        return right[0] <= float(value) <= right[1]
            if isinstance(right, str):
                value = value.replace(".", "").lower().strip()
                return value in right
            return False

        def has_days(s: str):
            return any([x in s for x in ["дней", "день", "дн.", "дня"]])

        def has_monthes(s: str):
            return any([x in s for x in ["месяцев", "месяц", "мес.", "м.", "месяца"]])

        def not_days_and_m(s: str):
            return not has_days(s) and not has_monthes(s)

        def has_years(s: str):
            return any([x in s for x in ["лет", "год", "л.", "года"]] + [not has_days(s) and not has_monthes(s)])

        def clc(r, val, age, only_ref):
            result = "normal"
            active_ref = {}
            if val.strip() != "":
                for k in r.keys():
                    tmp_result = "normal"
                    kk = re.sub("[^0-9\-]", "", k)
                    rigth = rigths(k.strip().lower())
                    rigthkk = rigths(kk)

                    if years == 0 and rigthkk and not has_years(k):
                        print(days, monthes, years, k)
                        if monthes == 0:
                            if has_days(k):
                                rigth = rigthkk
                                age = days
                            else:
                                rigth = [-1, -1]
                        else:
                            if has_monthes(k):
                                rigth = rigthkk
                                age = monthes
                            else:
                                rigth = [-1, -1]
                    elif not not_days_and_m(k):
                        rigth = [-1, -1]

                    if not rigth:
                        tmp_result = "maybe"
                    elif rigth[0] <= age <= rigth[1]:
                        if not only_ref:
                            rigth_v = rigths_v(r[k].strip().lower())
                            pattern = re.compile(r"^([a-zA-Zа-яА-Я]|\s|:|,|\^|@|\\|\||/|\+|-|\(|\)|\[|\]|{|}|#|№|!|~|\.)+$")
                            if pattern.match(r[k]):
                                if self.compare(r[k], val):
                                    tmp_result = "normal"
                                else:
                                    tmp_result = "not_normal"
                            elif rigth_v == "":
                                tmp_result = "maybe"
                            else:
                                test_v = test_value(rigth_v, val)
                                if not test_v:
                                    tmp_result = "not_normal"
                        else:
                            if raw_ref:
                                active_ref = {"k": k, "r": r[k]}
                            else:
                                active_ref = rigths_v(r[k].strip().lower())
                    if result not in ["maybe", "not_normal"] or tmp_result == "maybe":
                        result = tmp_result
            if only_ref:
                return active_ref
            return result

        calc = clc(ref, value, years, only_ref)
        return calc

    class Meta:
        verbose_name = 'Результат исследования'
        verbose_name_plural = 'Результаты исследований'

    @staticmethod
    def NFD(text):
        return unicodedata.normalize('NFD', text)

    def canonical_caseless(self, text):
        return self.NFD(self.NFD(text).casefold())

    def compare(self, a: str, b: str):
        a = a.strip()
        b = b.strip()

        return self.canonical_caseless(a) == self.canonical_caseless(b)


class DirectionToUserWatch(models.Model):
    direction = models.ForeignKey(Napravleniya, on_delete=models.CASCADE)
    doc = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE)


class DirectionsHistory(models.Model):
    direction = models.ForeignKey(Napravleniya, on_delete=models.CASCADE)
    old_card = models.ForeignKey(Clients.Card, related_name='old_card', help_text="Старая карта", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    new_card = models.ForeignKey(Clients.Card, related_name='new_card', help_text="Новая карта", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    old_fio_born = models.CharField(max_length=200, blank=True, help_text="ФИО д.р старой карты")
    new_fio_born = models.CharField(max_length=200, blank=True, help_text="ФИО д.р новой карты")
    date_change = models.DateTimeField(default=timezone.now, help_text='Время изменения владельца направления')
    who_change = models.ForeignKey(DoctorProfile, db_index=True, null=True, help_text='Кто изменил принадлежность направлений', on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'История принадлежности направления'
        verbose_name_plural = 'Принадлежности направления'

    @staticmethod
    def move_directions(old_card_number, new_card_number, user):
        old_card = Clients.Card.objects.filter(number=old_card_number, base__internal_type=True)[0]
        old_fio_born = old_card.get_fio_w_card()
        new_card = Clients.Card.objects.filter(number=new_card_number, base__internal_type=True)[0]
        new_fio_born = new_card.get_fio_w_card()
        with transaction.atomic():
            directions = Napravleniya.objects.select_for_update().filter(client=old_card)
            for dir in directions:
                dir.client = new_card
                dir.save()
                dir_history = DirectionsHistory(direction=dir, old_card=old_card, new_card=new_card, old_fio_born=old_fio_born, new_fio_born=new_fio_born, who_change=user)
                dir_history.save()

        return directions
