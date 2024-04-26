import inspect
import json
import math
import sys
from datetime import date, datetime
from typing import List, Union, Dict, Optional
import logging
import re

import simplejson
from dateutil.relativedelta import relativedelta
from django.core.exceptions import MultipleObjectsReturned
from django.core.management.base import OutputWrapper
from django.db import models, transaction
from django.db.models import Q
from django.db.models.signals import pre_save
from django.utils import timezone
from jsonfield import JSONField

import slog.models as slog
from appconf.manager import SettingManager
from clients.sql_func import last_result_researches_years
from directory.models import Researches, ScreeningPlan, PatientControlParam

from laboratory.utils import localtime, current_year, strfdatetime
from podrazdeleniya.models import Room
from users.models import Speciality, DoctorProfile, AssignmentTemplates
from django.contrib.postgres.fields import ArrayField

from utils.common import get_system_name
from utils.age import plural_age, MODE_DAYS, MODE_MONTHES, MODE_YEARS

TESTING = 'test' in sys.argv[1:] or 'jenkins' in sys.argv[1:]

logger = logging.getLogger(__name__)


class AgeCache(models.Model):
    n = models.IntegerField(db_index=True)
    t = models.IntegerField(db_index=True)
    s = models.CharField(max_length=30)

    def __str__(self):
        return self.s


class Individual(models.Model):
    family = models.CharField(max_length=120, blank=True, help_text="Фамилия", db_index=True)
    name = models.CharField(max_length=120, blank=True, help_text="Имя", db_index=True)
    patronymic = models.CharField(max_length=120, blank=True, help_text="Отчество", db_index=True)
    birthday = models.DateField(help_text="Дата рождения", db_index=True)
    sex = models.CharField(max_length=2, default="м", help_text="Пол", db_index=True)
    primary_for_rmis = models.BooleanField(default=False, blank=True)
    rmis_uid = models.CharField(max_length=64, default=None, null=True, blank=True)
    tfoms_idp = models.CharField(max_length=64, default=None, null=True, blank=True, db_index=True, help_text="ID в ТФОМС")
    tfoms_enp = models.CharField(max_length=64, default=None, null=True, blank=True, db_index=True, help_text="ENP в ТФОМС")
    time_tfoms_last_sync = models.DateTimeField(default=None, null=True, blank=True)
    ecp_id = models.CharField(max_length=64, default=None, null=True, blank=True, db_index=True, help_text="ID в ЕЦП")
    time_add = models.DateTimeField(default=timezone.now, null=True, blank=True)
    owner = models.ForeignKey('hospitals.Hospitals', default=None, blank=True, null=True, help_text="Организация-владелец данных", db_index=True, on_delete=models.PROTECT)
    owner_patient_id = models.CharField(max_length=128, default=None, null=True, blank=True, db_index=True, help_text="Код в организации-владелеце")

    def first(self):
        return self

    def join_individual(self, b: 'Individual', out: OutputWrapper = None):
        if out:
            out.write("Карт для переноса: %s" % Card.objects.filter(individual=b).count())
        slog.Log(key=str(self.pk), type=2002, body=simplejson.dumps({"Сохраняемая запись": str(self), "Объединяемая запись": str(b)}), user=None).save()
        for c in Card.objects.filter(individual=b):
            c.individual = self
            c.save()
        b.delete()

    def sync_with_rmis(self, out: OutputWrapper = None, c=None, force_print=False, forced_data=None):
        if not SettingManager.get("rmis_enabled", default='false', default_type='b') or not CardBase.objects.filter(is_rmis=True).exists():
            return
        if self.primary_for_rmis:
            self.reverse_sync()
            return
        if out:
            out.write("Обновление данных для: %s" % self.fio(full=True))
        if force_print:
            logger.exception("Обновление данных для: %s" % self.fio(full=True))
        if c is None:
            from rmis_integration.client import Client

            c = Client()
        ok = False
        has_rmis = False
        rmis_uid = ""
        if Card.objects.filter(individual=self, base__is_rmis=True).exists():
            rmis_uid = Card.objects.filter(individual=self, base__is_rmis=True)[0].number
            ok = has_rmis = True
            if out:
                out.write("Есть РМИС запись: %s" % rmis_uid)
            if force_print:
                logger.exception("Есть РМИС запись: %s" % rmis_uid)

        founded_by_uid = {}

        if not ok:
            docs = Document.objects.filter(individual=self).exclude(document_type__check_priority=0).order_by("-document_type__check_priority")
            for document in docs:
                s = c.patients.search_by_document(document)
                for x in s:
                    data = c.patients.get_data(rmis_uid, forced_data=forced_data, return_none_on_empty=True)
                    if data:
                        founded_by_uid[x] = data
                        rmis_uid = x
                        ok = True
                        if out:
                            out.write("Физ.лицо найдено по документу: %s -> %s" % (document, rmis_uid))
                            if force_print:
                                logger.exception("Физ.лицо найдено по документу: %s -> %s" % (document, rmis_uid))
                        break
                if ok:
                    break

        if ok:
            data = founded_by_uid.get('rmis_uid') or c.patients.get_data(rmis_uid, forced_data=forced_data, return_none_on_empty=True)
            if data:
                upd = (
                    self.family != data["family"]
                    or self.name != data["name"]
                    or self.patronymic != data["patronymic"]
                    or (self.birthday != data["birthday"] and data["birthday"] is not None)
                )

                if upd:
                    prev = str(self)
                    self.family = data["family"]
                    self.name = data["name"]
                    self.patronymic = data["patronymic"]
                    if data["birthday"] is not None:
                        self.birthday = data["birthday"]
                    self.sex = data["sex"]
                    self.save()
                    if out:
                        out.write("Обновление данных: %s" % self.fio(full=True))
                    if force_print:
                        logger.exception("Обновление данных: %s" % self.fio(full=True))
                    slog.Log(key=str(self.pk), type=2003, body=simplejson.dumps({"Новые данные": str(self), "Не актуальные данные": prev}), user=None).save()

        if not ok:
            query = {"surname": self.family, "name": self.name, "patrName": self.patronymic, "birthDate": self.birthday.strftime("%Y-%m-%d")}
            rows = c.patients.client.searchIndividual(**query)
            if len(rows) == 1:
                rmis_uid = rows[0]
                ok = True
                if out:
                    out.write("Физ.лицо найдено по ФИО и д.р.: %s" % rmis_uid)
                if force_print:
                    logger.exception("Физ.лицо найдено по ФИО и д.р.: %s" % rmis_uid)

        if not has_rmis and rmis_uid and rmis_uid != '':
            ex = Card.objects.filter(number=rmis_uid, is_archive=False, base__is_rmis=True)
            if ex.exists():
                for e in ex:
                    self.join_individual(e.individual, out)
            s = str(c.patients.create_rmis_card(self, rmis_uid))
            if out:
                out.write("Добавление РМИС карты -> %s" % s)
            if force_print:
                logger.exception("Добавление РМИС карты -> %s" % s)

        save_docs = []

        if ok and rmis_uid != "" and Card.objects.filter(individual=self, base__is_rmis=True, is_archive=False).exists():
            pat_data = c.patients.extended_data(rmis_uid)
            cards = Card.objects.filter(individual=self, base__is_rmis=True, is_archive=False)
            for card_i in cards:
                c.patients.sync_card_data(card_i, out)

            def get_key(d: dict, val):
                r = [key for key, v in d.items() if v == val]
                if len(r) > 0:
                    return r[0]
                return None

            def get_key_reverse(d: dict, val):
                return d.get(val)

            if out:
                out.write("Типы документов: %s" % simplejson.dumps(c.patients.local_types))

            for document_object in pat_data["identifiers"] if "identifiers" in pat_data else []:
                k = get_key(c.patients.local_types, document_object["type"])
                if not k:
                    k = get_key_reverse(c.patients.local_reverse_types, document_object["type"])
                if k and document_object["active"]:
                    if out:
                        out.write("Тип: %s -> %s (%s)" % (document_object["type"], k, document_object["active"]))
                    data = dict(
                        document_type=DocumentType.objects.get(pk=k),
                        serial=document_object["series"] or "",
                        number=document_object["number"] or "",
                        date_start=document_object["issueDate"],
                        date_end=document_object["expiryDate"],
                        who_give=(document_object["issueOrganization"] or {"name": document_object["issuerText"] or ""})["name"] or "",
                        individual=self,
                        is_active=True,
                    )
                    rowss = Document.objects.filter(document_type=data['document_type'], individual=self, from_rmis=True)
                    if rowss.exclude(serial=data["serial"]).exclude(number=data["number"]).filter(card__isnull=True).exists():
                        Document.objects.filter(document_type=data['document_type'], individual=self, from_rmis=True).delete()
                    docs = Document.objects.filter(document_type=data['document_type'], serial=data['serial'], number=data['number'], from_rmis=True)
                    if not docs.exists():
                        doc = Document(**data)
                        doc.save()
                        if out:
                            out.write("Добавление документа: %s" % doc)
                        kk = "%s_%s_%s" % (doc.document_type_id, doc.serial, doc.number)
                        save_docs.append(kk)
                        continue
                    else:
                        to_delete = []
                        has = []
                        ndocs = {}
                        for d in docs:
                            kk = "%s_%s_%s" % (d.document_type_id, d.serial, d.number)
                            if out:
                                out.write("Checking: %s" % kk)
                            if kk in has:
                                if out:
                                    out.write("to delete: %s" % d.pk)
                                to_delete.append(d.pk)
                                if Card.objects.filter(polis=d).exists():
                                    for c in Card.objects.filter(polis=d):
                                        c.polis = ndocs[kk]
                                        c.save()
                            else:
                                if out:
                                    out.write("To has: %s" % d.pk)
                                has.append(kk)
                                save_docs.append(kk)
                                ndocs[kk] = d

                        Document.objects.filter(pk__in=to_delete).delete()
                        docs = Document.objects.filter(document_type=data['document_type'], serial=data['serial'], number=data['number'], individual=self)
                        for d in docs:
                            if d.date_start != data["date_start"]:
                                d.date_start = data["date_start"]
                                d.save()
                                if out:
                                    out.write("Update date_start: %s" % d.date_start)
                            if d.date_end != data["date_end"]:
                                d.date_end = data["date_end"]
                                d.save()
                                if out:
                                    out.write("Update date_end: %s" % d.date_end)
                            if d.who_give != data["who_give"]:
                                d.who_give = data["who_give"]
                                d.save()
                                if out:
                                    out.write("Update who_give: %s" % d.who_give)

                        if out:
                            out.write("Данные для документов верны: %s" % [str(x) for x in docs])

                    docs = (
                        Document.objects.filter(
                            document_type=data['document_type'], document_type__title__in=['СНИЛС', 'Паспорт гражданина РФ', 'Полис ОМС'], serial=data['serial'], number=data['number']
                        )
                        .exclude(individual=self)
                        .exclude(number="")
                    )
                    if docs.exists():
                        if out:
                            out.write("Объединение записей физ.лиц")
                        for doc in docs:
                            self.join_individual(doc.individual, out)

            to_delete_pks = []
            for d in Document.objects.filter(individual=self, from_rmis=True):
                kk = "%s_%s_%s" % (d.document_type_id, d.serial, d.number)
                if out:
                    out.write(
                        "TD %s %s %s"
                        % (
                            kk,
                            kk not in save_docs,
                            save_docs,
                        )
                    )
                if kk not in save_docs:
                    to_delete_pks.append(d.pk)
            Document.objects.filter(pk__in=to_delete_pks).delete()
        else:
            self.primary_for_rmis = True
            self.save()
            self.reverse_sync()
            if out:
                out.write("Физ.лицо не найдено в РМИС")
            if force_print:
                logger.exception("Физ.лицо не найдено в РМИС")
        return ok

    def reverse_sync(self, force_new=False):
        from rmis_integration.client import Client

        c = Client(modules=['patients', 'individuals'])
        cards = Card.objects.filter(individual=self, base__is_rmis=True, is_archive=False)
        n = False
        if not cards.exists() or not self.rmis_uid or force_new:
            ind_uid, rmis_uid = c.patients.send_new_patient(self)
            self.rmis_uid = ind_uid
            self.save()
            c.patients.create_rmis_card(self, rmis_uid)
            cards = Card.objects.filter(number=rmis_uid)
            n = True
        card = cards[0]
        pat_data = c.patients.extended_data(card.number)
        if "patient" not in pat_data:
            if not force_new:
                self.reverse_sync(force_new=True)
        elif not n:
            p = pat_data["patient"]
            g = {"ж": "2"}.get(self.sex.lower(), "1")
            if self.family != p["lastName"] or self.name != p["firstName"] or self.patronymic != p["middleName"] or self.sex != g or self.birthday != self.birthday:
                c.patients.edit_patient(self)

    def bd(self):
        return "{:%d.%m.%Y}".format(self.birthday)

    # подсчет возраста в рамках года
    def age_for_year(self):
        year_today = current_year()
        last_date = datetime.strptime(f'31.12.{year_today}', '%d.%m.%Y').date()
        born_date = self.birthday
        return last_date.year - born_date.year - ((last_date.month, last_date.day) < (born_date.month, born_date.day))

    def age(self, iss=None, days_monthes_years=False, target_date=None):
        """
        Функция подсчета возраста
        """
        if not target_date:
            if (
                iss is None
                or (not iss.tubes.exists() and not iss.time_confirmation)
                or ((not iss.tubes.exists() or not iss.tubes.filter(time_recive__isnull=False).exists()) and not iss.research.is_paraclinic and not iss.research.is_doc_refferal)
            ):
                today = date.today()
            elif iss.time_confirmation and (iss.research.is_paraclinic or iss.research.is_doc_refferal) or not iss.tubes.exists():
                today = iss.time_confirmation.date()
            else:
                today = iss.tubes.filter(time_recive__isnull=False).order_by("-time_recive")[0].time_recive.date()
        else:
            today = target_date
            if isinstance(today, str):
                today = datetime.strptime(today, "%d.%m.%Y" if '.' in today else "%Y-%m-%d").date()
        born = self.birthday
        if isinstance(born, str):
            born = datetime.strptime(born, "%d.%m.%Y" if '.' in born else "%Y-%m-%d").date()
        try:
            birthday = born.replace(year=today.year)
        except ValueError:
            birthday = born.replace(year=today.year, month=born.month + 1, day=1)

        if birthday > today:
            if days_monthes_years:
                rd = relativedelta(today, born)
                return rd.days, rd.months, rd.years
            return today.year - born.year
        else:
            if days_monthes_years:
                rd = relativedelta(today, born)
                return rd.days, rd.months, rd.years
            return today.year - born.year

    def age_s(self, iss=None, direction=None) -> str:
        """
        Формирование строки возраста: 10 лет, 101 год
        :return:
        """
        if direction is not None:
            from directions.models import Issledovaniya

            iss = None
            i = Issledovaniya.objects.filter(tubes__time_recive__isnull=False, napravleniye=direction).order_by("-tubes__time_recive")
            if i.exists():
                iss = i[0]
            elif Issledovaniya.objects.filter(research__is_paraclinic=True, napravleniye=direction, time_confirmation__isnull=False):
                iss = Issledovaniya.objects.filter(research__is_paraclinic=True, napravleniye=direction, time_confirmation__isnull=False).order_by("-time_confirmation")[0]

        days, monthes, years = self.age(iss=iss, days_monthes_years=True)

        if years > 0:
            age = years
            ages = AgeCache.objects.filter(n=age, t=0)
            if ages.exists():
                r = ages[0].s
            else:
                r = plural_age(age, mode=MODE_YEARS)
                AgeCache(n=age, t=0, s=r).save()
        elif monthes > 0:
            age = monthes
            ages = AgeCache.objects.filter(n=age, t=1)

            if ages.exists():
                r = ages[0].s
            else:
                r = plural_age(age, mode=MODE_MONTHES)
                AgeCache(n=age, t=1, s=r).save()
        else:
            age = days
            ages = AgeCache.objects.filter(n=age, t=2)

            if ages.exists():
                r = ages[0].s
            else:
                r = plural_age(age, mode=MODE_DAYS)
                AgeCache(n=age, t=2, s=r).save()
        return r

    def fio(self, short=False, dots=False, full=False, direction=None, npf=False, bd=False):
        if not short:
            birthday_date = datetime.strptime(self.birthday, "%d.%m.%Y" if '.' in self.birthday else "%Y-%m-%d").date() if isinstance(self.birthday, str) else self.birthday
            if full:
                r = "{0} {1} {2}, {5}, {3:%d.%m.%Y} ({4})".format(self.family, self.name, self.patronymic, birthday_date, self.age_s(direction=direction), self.sex)
            elif not npf:
                r = "{} {} {}".format(self.family, self.name, self.patronymic).strip()
            elif bd:
                r = "{0} {1} {2}, {3:%d.%m.%Y}".format(self.family, self.name, self.patronymic, birthday_date)
            else:
                r = "{} {} {}".format(self.name, self.patronymic, self.family).strip()
        else:

            def first_letter_not_blank(s):
                if len(s) > 0:
                    return " " + s[0] + ("." if dots else "")
                return ""

            r = "{0}{1}".format(self.family, first_letter_not_blank(self.name) + first_letter_not_blank(self.patronymic).replace(" ", "" if not dots else " "))
        return r.strip()

    def __str__(self):
        return self.fio(full=True)

    def check_rmis(self, update=True, client=None):
        from rmis_integration.client import Client

        if client is None:
            client = Client()
        rmis_id = client.patients.get_rmis_id_for_individual(individual=self)
        if rmis_id and rmis_id != 'NONERMIS':
            from directions.models import Napravleniya

            Napravleniya.objects.filter(client__individual=self, rmis_number='NONERMIS').update(rmis_number=None)
        return rmis_id

    def get_rmis_uid(self):
        if not Card.objects.filter(base__is_rmis=True, is_archive=False, individual=self).exists():
            return self.check_rmis()
        return self.check_rmis(False)

    def get_rmis_uid_fast(self):
        if Card.objects.filter(base__is_rmis=True, is_archive=False, individual=self).exists():
            return Card.objects.filter(base__is_rmis=True, is_archive=False, individual=self)[0].number
        return ""

    def get_enp(self):
        enp_doc: Union[Document, None] = Document.objects.filter(document_type__title__startswith="Полис ОМС", individual=self).first()
        if enp_doc and enp_doc.number:
            return enp_doc.number
        return None

    def sync_with_tfoms(self):
        is_new = False
        updated = []

        enp_doc: Union[Document, None] = Document.objects.filter(document_type__title__startswith="Полис ОМС", individual=self).first()

        tfoms_data = None
        if enp_doc and enp_doc.number:
            from tfoms.integration import match_enp

            tfoms_data = match_enp(enp_doc.number)

        if not tfoms_data:
            from tfoms.integration import match_patient

            tfoms_data = match_patient(self.family, self.name, self.patronymic, strfdatetime(self.birthday, '%Y-%m-%d'))

        if tfoms_data:
            is_new = not bool(self.tfoms_idp or self.tfoms_enp)
            updated = Individual.import_from_tfoms(tfoms_data, self)

        return is_new, updated

    def match_tfoms(self):
        enp_doc: Union[Document, None] = Document.objects.filter(document_type__title__startswith="Полис ОМС", individual=self).first()

        tfoms_data = None
        if enp_doc and enp_doc.number:
            from tfoms.integration import match_enp

            tfoms_data = match_enp(enp_doc.number)

        if not tfoms_data:
            from tfoms.integration import match_patient

            tfoms_data = match_patient(self.family, self.name, self.patronymic, strfdatetime(self.birthday, '%Y-%m-%d'))

            tfoms_data = None if not isinstance(tfoms_data, list) or len(tfoms_data) == 0 else tfoms_data[0]

        return tfoms_data

    @staticmethod
    def import_from_ecp(patient_data: dict):
        individual = Individual.objects.filter(ecp_id=patient_data['Person_id']).first()
        snils_type = DocumentType.objects.filter(title__startswith="СНИЛС").first()
        enp_type = DocumentType.objects.filter(title__startswith="Полис ОМС").first()

        if not individual:
            if snils_type and patient_data.get('PersonSnils_Snils'):
                individual = Individual.objects.filter(document__document_type=snils_type, document__number=patient_data['PersonSnils_Snils']).first()
            if not individual and enp_type and patient_data.get('enp'):
                individual = Individual.objects.filter(document__document_type=enp_type, document__number=patient_data['enp']).first()

        sex = 'ж' if patient_data['Person_Sex_id'] == '2' else 'м'
        if not individual:
            individual = Individual(
                ecp_id=patient_data['Person_id'],
                family=patient_data['PersonSurName_SurName'],
                name=patient_data['PersonFirName_FirName'],
                patronymic=patient_data['PersonSecName_SecName'],
                birthday=patient_data['PersonBirthDay_BirthDay'],
                sex=sex,
            )
            individual.save()
        else:
            individual.family = patient_data['PersonSurName_SurName']
            individual.name = patient_data['PersonFirName_FirName']
            individual.patronymic = patient_data['PersonSecName_SecName']
            individual.birthday = patient_data['PersonBirthDay_BirthDay']
            individual.sex = sex
            individual.ecp_id = patient_data['Person_id']
            individual.save(update_fields=['family', 'name', 'patronymic', 'birthday', 'sex', 'ecp_id'])

        snils_doc = None
        if snils_type and patient_data.get('PersonSnils_Snils'):
            snils = patient_data['PersonSnils_Snils']
            snils = ''.join([s for s in snils if s.isdigit()])
            if not Document.objects.filter(individual=individual, document_type=snils_type).exists():
                snils_doc = Document(
                    individual=individual,
                    document_type=snils_type,
                    number=snils,
                )
                snils_doc.save()
            else:
                snils_doc = Document.objects.filter(individual=individual, document_type=snils_type).first()
                snils_doc.number = snils
                snils_doc.save(update_fields=['number'])

        enp_doc = None
        if enp_type and patient_data.get('enp'):
            enp = patient_data['enp']
            if not Document.objects.filter(individual=individual, document_type=enp_type).exists():
                enp_doc = Document(
                    individual=individual,
                    document_type=enp_type,
                    number=enp,
                )
                enp_doc.save()
            else:
                enp_doc = Document.objects.filter(individual=individual, document_type=enp_type).first()
                enp_doc.number = enp
                enp_doc.save(update_fields=['number'])

        if not Card.objects.filter(base__internal_type=True, individual=individual, is_archive=False).exists():
            Card.add_l2_card(individual, polis=enp_doc, snils=snils_doc)
        else:
            card = Card.objects.filter(base__internal_type=True, individual=individual, is_archive=False).first()
            if enp_doc:
                cdu = CardDocUsage.objects.filter(card=card, document__document_type=enp_doc.document_type)
                if not cdu.exists():
                    if cdu:
                        if cdu.first().document != enp_doc:
                            cdu.first().document = enp_doc
                            cdu.first().save(update_fields=['document'])
                    else:
                        CardDocUsage(card=card, document=enp_doc).save()
            if snils_doc:
                cdu = CardDocUsage.objects.filter(card=card, document__document_type=snils_doc.document_type)
                if not cdu.exists():
                    if cdu:
                        if cdu.first().document != snils_doc:
                            cdu.first().document = snils_doc
                            cdu.first().save(update_fields=['document'])
                    else:
                        CardDocUsage(card=card, document=snils_doc).save()
        return individual

    @staticmethod
    def import_from_tfoms(data: Union[dict, List], individual: Union['Individual', None] = None, no_update=False, need_return_individual=False, need_return_card=False):
        if isinstance(data, list):
            if len(data) > 0:
                data = data[0]
            else:
                data = {}
        idp = data.get('idp')
        updated_data = []

        family = data.get('family', '').title().strip()
        name = data.get('given', '').title().strip()
        patronymic = data.get('patronymic', '').title().strip()
        gender = data.get('gender', '').lower().strip()
        bdate = data.get('birthdate', '').split(' ')[0]
        insurer_full_code = data.get('insurer_full_code', '')

        if gender == 'm':
            gender = 'м'

        if gender == 'f':
            gender = 'ж'

        i = None
        card = None

        if family and name and gender and bdate:
            passport_type = DocumentType.objects.filter(title__startswith="Паспорт гражданина РФ").first()
            birth_cert_type = DocumentType.objects.filter(title__startswith="Свидетельство о рождении").first()
            enp = (data.get('enp') or '').strip()
            birthday = datetime.strptime(bdate, "%d.%m.%Y" if '.' in bdate else "%Y-%m-%d").date()
            address = data.get('address', '').title().replace('Ул.', 'ул.').replace('Д.', 'д.').replace('Кв.', 'кв.').strip()
            document_type = data.get('document_type', '').strip()
            document_seria = data.get('document_seria', '').strip()
            document_number = data.get('document_number', '').strip()
            birth_cert_number, birth_cert_seria, passport_number, passport_seria = None, None, None, None
            if birth_cert_type and document_type == birth_cert_type.tfoms_type:
                birth_cert_number = document_number
                birth_cert_seria = document_seria
            elif passport_type and document_type == passport_type.tfoms_type:
                passport_number = document_number
                passport_seria = document_seria
            if not document_type:
                passport_number = data.get('passport_number', '').strip()
                passport_serial = data.get('passport_serial', '').strip()
                passport_seria = passport_serial or data.get('passport_seria', '').strip()
                if len(passport_seria.split('-')) > 1:
                    birth_cert_number = passport_number
                    birth_cert_seria = passport_seria
            snils = (data.get('snils') or '').replace(' ', '').replace('-', '')

            q_idp = dict(tfoms_idp=idp or '##fakeidp##')
            q_enp = dict(tfoms_enp=enp or '##fakeenp##')

            if not individual:
                if enp:
                    q_more = dict(document__document_type__title='Полис ОМС', document__number=enp)
                else:
                    q_more = {}
                if idp or enp or snils:
                    indv = (
                        Individual.objects.filter(Q(**q_idp) | Q(**q_enp) | Q(document__document_type__title='СНИЛС', document__number=snils) | Q(**q_more))
                        if snils
                        else Individual.objects.filter(Q(**q_idp) | Q(**q_enp) | Q(**q_more))
                    )
                else:
                    indv = None
            else:
                indv = Individual.objects.filter(pk=individual.pk)

            enp_type = DocumentType.objects.filter(title__startswith="Полис ОМС").first()

            if not indv or not indv.exists():
                i = Individual(
                    family=family,
                    name=name,
                    patronymic=patronymic,
                    birthday=birthday,
                    sex=gender,
                    tfoms_idp=idp,
                    tfoms_enp=enp,
                )
                i.save()
            else:
                i = indv[0]
                ce = Card.objects.filter(individual=i, base__internal_type=True).first()
                if no_update and ce:
                    print('No update')  # noqa: T001
                    polis = i.add_or_update_doc(enp_type, '', enp, insurer_full_code)
                    if polis:
                        cdu = CardDocUsage.objects.filter(card=ce, document__document_type=polis.document_type)
                        if not cdu.exists():
                            CardDocUsage(card=ce, document=polis).save()
                        else:
                            for c in cdu:
                                c.document = polis
                                c.save(update_fields=["document"])
                    return
                print('Update patient data')  # noqa: T001
                updated = []

                if i.family != family:
                    i.family = family
                    updated.append('family')
                    updated_data.append('Фамилия')

                if i.name != name:
                    i.name = name
                    updated.append('name')
                    updated_data.append('Имя')

                if i.patronymic != patronymic:
                    i.patronymic = patronymic
                    updated.append('patronymic')
                    updated_data.append('Отчество')

                if i.sex != gender:
                    i.sex = gender
                    updated.append('sex')
                    updated_data.append('Пол')

                if i.birthday != birthday:
                    i.birthday = birthday
                    updated.append('birthday')
                    updated_data.append('Дата рождения')

                if idp and i.tfoms_idp != idp:
                    i.tfoms_idp = idp
                    updated.append('tfoms_idp')

                if enp and i.tfoms_enp != enp:
                    i.tfoms_enp = enp
                    updated.append('tfoms_enp')

                if updated:
                    print('Updated:', updated)  # noqa: T001
                    i.save(update_fields=updated)

            print(i)  # noqa: T001

            print('Sync documents')  # noqa: T001

            enp_type = DocumentType.objects.filter(title__startswith="Полис ОМС").first()
            snils_type = DocumentType.objects.filter(title__startswith="СНИЛС").first()

            if snils_type and snils:
                print('Sync SNILS')  # noqa: T001
                i.add_or_update_doc(snils_type, '', snils)

            if birth_cert_type and birth_cert_seria and birth_cert_number:
                i.add_or_update_doc(birth_cert_type, birth_cert_seria, birth_cert_number)
            elif passport_type and passport_seria and passport_number:
                print('Sync PASSPORT')  # noqa: T001
                i.add_or_update_doc(passport_type, passport_seria, passport_number)

            enp_doc = None
            if enp_type and enp:
                print('Sync ENP')  # noqa: T001
                enp_doc = i.add_or_update_doc(enp_type, '', enp, insurer_full_code)

            print('Sync L2 card')  # noqa: T001
            card = Card.add_l2_card(individual=i, polis=enp_doc, address=address, force=True, updated_data=updated_data)
            print(card)  # noqa: T001

            card.get_card_documents()

            i.time_tfoms_last_sync = timezone.now()
            i.save(update_fields=['time_tfoms_last_sync'])

        if need_return_individual:
            return i

        if need_return_card:
            return card

        return updated_data

    @staticmethod
    def import_from_simple_data(data: dict, owner, patient_id_company, email, phone):
        family = data.get('family', '').title().strip()
        name = data.get('name', '').title().strip()
        patronymic = data.get('patronymic', '').title().strip()
        sex = data.get('sex', '').lower().strip()
        birthday = data.get('birthday', '').split(' ')[0]
        snils = data.get('snils', '').split(' ')[0]

        i = None
        card = None

        if family and name and sex and birthday:
            birthday = datetime.strptime(birthday, "%d.%m.%Y" if '.' in birthday else "%Y-%m-%d").date()

            indv = Individual.objects.filter(
                family=family,
                name=name,
                patronymic=patronymic,
                birthday=birthday,
                sex=sex,
                owner=owner,
            )

            if not indv or not indv.exists():
                i = Individual(
                    family=family,
                    name=name,
                    patronymic=patronymic,
                    birthday=birthday,
                    sex=sex,
                    owner=owner,
                    owner_patient_id=patient_id_company,
                )
                i.save()
            else:
                i = indv.first()
                updated = []

                if i.family != family:
                    i.family = family
                    updated.append('family')

                if i.name != name:
                    i.name = name
                    updated.append('name')

                if i.patronymic != patronymic:
                    i.patronymic = patronymic
                    updated.append('patronymic')

                if i.sex != sex:
                    i.sex = sex
                    updated.append('sex')

                if i.birthday != birthday:
                    i.birthday = birthday
                    updated.append('birthday')

                if updated:
                    i.save(update_fields=updated)

        if i:
            snils_type = DocumentType.objects.filter(title__startswith="СНИЛС").first()
            document_snils = i.add_or_update_doc(snils_type, '', snils)
            card = Card.add_l2_card(individual=i, force=True, owner=owner, snils=document_snils)

        return card

    def add_or_update_doc(self, doc_type: 'DocumentType', serial: str, number: str, insurer_full_code=""):
        ds = Document.objects.filter(individual=self, document_type=doc_type, is_active=True)
        if ds.count() > 1:
            ds.delete()

        ds = Document.objects.filter(individual=self, document_type=doc_type, is_active=True)
        if ds.count() == 0:
            d = Document(individual=self, document_type=doc_type, serial=serial, number=number, insurer_full_code=insurer_full_code)
            d.save()
        else:
            d: Document = ds.first()
            updated = []

            if d.serial != serial:
                d.serial = serial
                updated.append('serial')

            if d.number != number:
                d.number = number
                updated.append('number')
            if d.insurer_full_code != insurer_full_code:
                d.insurer_full_code = insurer_full_code
                updated.append('insurer_full_code')

            if updated:
                d.save(update_fields=updated)
        return d

    class Meta:
        verbose_name = 'Физическое лицо'
        verbose_name_plural = 'Физические лица'


class DocumentType(models.Model):
    title = models.CharField(max_length=60, help_text="Название типа документа")
    check_priority = models.IntegerField(default=0, help_text="Приоритет проверки документа (чем больше число - тем больше (сильнее) приоритет)")
    rmis_type = models.CharField(max_length=10, default=None, blank=True, null=True)
    tfoms_type = models.CharField(max_length=10, default=None, blank=True, null=True)

    def __str__(self):
        return "{} | {} | ^{}".format(self.pk, self.title, self.check_priority)

    @property
    def n3_type(self):
        title = self.title.lower().strip()
        if 'снилс' in title:
            return 'snils'
        if 'паспорт гражданина рф' in title:
            return 'passport'
        if 'полис омс' in title:
            return 'enp'
        return None

    class Meta:
        verbose_name = 'Вид документа'
        verbose_name_plural = 'Виды документов'


class Document(models.Model):
    document_type = models.ForeignKey(DocumentType, help_text="Тип документа", db_index=True, on_delete=models.CASCADE)
    serial = models.CharField(max_length=30, blank=True, help_text="Серия")
    number = models.CharField(max_length=30, blank=True, help_text="Номер")
    individual = models.ForeignKey(Individual, help_text="Пациент", db_index=True, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True, blank=True, help_text="Документ активен")
    date_start = models.DateField(help_text="Дата начала действия документа", blank=True, null=True)
    date_end = models.DateField(help_text="Дата окончания действия документа", blank=True, null=True)
    who_give = models.TextField(default="", blank=True, help_text="Кто выдал")
    from_rmis = models.BooleanField(default=True, blank=True)
    rmis_uid = models.CharField(max_length=11, default=None, blank=True, null=True)
    insurer_full_code = models.CharField(max_length=11, default="", blank=True, null=True, help_text="Код страховой")

    @property
    def date_start_local(self):
        return localtime(self.date_start)

    @property
    def date_end_local(self):
        return localtime(self.date_end)

    def __str__(self):
        return "{0} {1} {2}".format(self.document_type, self.serial, self.number)

    @staticmethod
    def get_all_doc(docs):
        """
        Возвращает словарь словарей documents. Данные о документах: паспорт : номер: серия, полис: номер, снислс: номер
        """
        documents = {
            'passport': {'num': "", 'serial': "", 'date_start': "", 'issued': ""},
            'polis': {'serial': "", 'num': "", 'issued': "", "insurer_full_code": ""},
            'snils': {'num': ""},
            'bc': {'num': "", 'serial': "", 'date_start': "", 'issued': ""},
        }

        for d in docs:
            if d.document_type.title == "СНИЛС":
                documents["snils"]["num"] = d.number

            if d.document_type.title == 'Паспорт гражданина РФ':
                documents["passport"]["num"] = d.number
                documents["passport"]["serial"] = d.serial
                documents["passport"]["date_start"] = "" if not d.date_start else d.date_start.strftime("%d.%m.%Y")
                documents["passport"]["issued"] = d.who_give

            if d.document_type.title == 'Полис ОМС':
                documents["polis"]["num"] = d.number
                documents["polis"]["serial"] = d.serial
                documents["polis"]["date_start"] = "" if not d.date_start else d.date_start.strftime("%d.%m.%Y")
                documents["polis"]["issued"] = d.who_give
                documents["polis"]["insurer_full_code"] = d.insurer_full_code

            if d.document_type.title == 'Свидетельство о рождении':
                documents["bc"]["num"] = d.number
                documents["bc"]["serial"] = d.serial
                documents["bc"]["date_start"] = "" if not d.date_start else d.date_start.strftime("%d.%m.%Y")
                documents["bc"]["issued"] = d.who_give

        return documents

    def sync_rmis(self):
        if self.individual.primary_for_rmis and not self.from_rmis and self.individual.rmis_uid and self.document_type.rmis_type:
            from rmis_integration.client import Client

            c = Client(modules=['patients', 'individuals'])
            cards = Card.objects.filter(individual=self.individual, base__is_rmis=True, is_archive=False)
            if not cards.exists():
                return
            # card = cards[0]
            if self.rmis_uid:
                d = c.individuals.client.getDocument(self.rmis_uid)
                if (
                    d["series"] != self.serial
                    or d['number'] != self.number
                    or d['issuerText'] != self.who_give
                    or d['issueDate'] != self.date_start
                    or d['expireDate'] != self.date_end
                    or d['active'] != self.is_active
                ):
                    data = {
                        "documentId": self.rmis_uid,
                        "documentData": {
                            "individualUid": self.individual.rmis_uid,
                            "type": self.document_type.rmis_type,
                            "issuerText": self.who_give,
                            "series": self.serial,
                            "number": self.number,
                            "active": self.is_active,
                            "issueDate": self.date_start,
                            "expireDate": self.date_end,
                        },
                    }
                    d = c.individuals.client.editDocument(**data)
            else:
                data = {
                    "individualUid": self.individual.rmis_uid,
                    "type": self.document_type.rmis_type,
                    "issuerText": self.who_give,
                    "series": self.serial,
                    "number": self.number,
                    "active": self.is_active,
                    "issueDate": self.date_start,
                    "expireDate": self.date_end,
                }
                d = c.individuals.client.createDocument(**data)
                self.rmis_uid = d
                self.save()

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'


class CardDocUsage(models.Model):
    card = models.ForeignKey('clients.Card', db_index=True, on_delete=models.CASCADE)
    document = models.ForeignKey('clients.Document', db_index=True, on_delete=models.CASCADE, help_text='Используемый документ карты')


class CardBase(models.Model):
    title = models.CharField(max_length=50, help_text="Полное название базы")
    short_title = models.CharField(max_length=4, help_text="Краткий код базы", db_index=True)
    is_rmis = models.BooleanField(help_text="Это РМИС?", default=False)
    hide = models.BooleanField(help_text="Скрыть базу", default=False)
    history_number = models.BooleanField(help_text="Ввод номера истории", default=False)
    internal_type = models.BooleanField(help_text="Внутренний тип карт", default=False)
    assign_in_search = models.ForeignKey(
        "clients.CardBase",
        related_name="assign_in_search_base",
        help_text="Показывать результаты в поиске вместе с этой базой",
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    order_weight = models.SmallIntegerField(default=0)
    forbidden_create_napr = models.BooleanField(help_text="Запрет создания направлений", default=False)

    def get_fin_sources(self):
        return [{'id': x.pk, 'label': x.title} for x in self.istochnikifinansirovaniya_set.filter(hide=False).order_by('-order_weight')]

    def __str__(self):
        return "{0} - {1}".format(self.title, self.short_title)

    class Meta:
        verbose_name = 'База карт'
        verbose_name_plural = 'Базы карт'


class District(models.Model):
    title = models.CharField(max_length=128)
    sort_weight = models.IntegerField(default=0, null=True, blank=True, help_text='Вес сортировки')
    is_ginekolog = models.BooleanField(help_text="Гинекологический участок", default=False)
    code_poliklinika = models.CharField(max_length=8, default='', help_text="Краткий код участка", db_index=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Участок'
        verbose_name_plural = 'Участки'


class HarmfulFactor(models.Model):
    title = models.CharField(max_length=255, help_text='Наименование')
    description = models.CharField(max_length=1024, help_text='Описание', blank=True, default=None, null=True)
    template = models.ForeignKey(AssignmentTemplates, db_index=True, null=True, blank=True, default=None, on_delete=models.CASCADE)
    cpp_key = models.UUIDField(null=True, blank=True, editable=False, help_text="UUID, с справочника", db_index=True)
    nsi_id = models.CharField(max_length=128, db_index=True, blank=True, default=None, null=True)
    nsi_title = models.CharField(max_length=255, blank=True, default=None, null=True, help_text='НСИ-наименование')

    class Meta:
        verbose_name = 'Фактор вредности'
        verbose_name_plural = 'Факторы вредности'

    @staticmethod
    def get_template_by_factor(factor_pks):
        factors = HarmfulFactor.objects.filter(pk__in=factor_pks)
        return [i.template.pk for i in factors]

    @staticmethod
    def as_json(factor):
        json = {
            "id": factor.pk,
            "title": factor.title,
            "description": factor.description,
            "template_id": factor.template_id,
        }
        return json


class Card(models.Model):
    AGENT_CHOICES = (
        ('mother', "Мать"),
        ('father', "Отец"),
        ('curator', "Опекун"),
        ('agent', "Представитель"),
        ('payer', "Плательщик"),
        ('', 'НЕ ВЫБРАНО'),
    )

    MEDBOOK_TYPES = (
        ('none', 'нет'),
        ('auto', 'авто'),
        ('custom', 'вручную'),
    )

    AGENT_NEED_DOC = ['curator', 'agent']
    AGENT_CANT_SELECT = ['payer']

    number = models.CharField(max_length=20, blank=True, help_text="Идентификатор карты", db_index=True)
    base = models.ForeignKey(CardBase, help_text="База карты", db_index=True, on_delete=models.PROTECT)
    individual = models.ForeignKey(Individual, help_text="Пациент", db_index=True, on_delete=models.PROTECT)
    is_archive = models.BooleanField(default=False, blank=True, db_index=True, help_text="Карта в архиве")
    polis = models.ForeignKey(Document, help_text="Документ для карты", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    main_diagnosis = models.CharField(max_length=36, blank=True, default='', help_text="Основной диагноз", db_index=True)
    main_address = models.CharField(max_length=128, blank=True, default='', help_text="Адрес регистрации")
    main_address_fias = models.CharField(max_length=128, blank=True, default=None, null=True, help_text="ФИАС Адрес регистрации")
    main_address_details = JSONField(blank=True, null=True, help_text="Детали адреса регистрации")
    fact_address = models.CharField(max_length=128, blank=True, default='', help_text="Адрес факт. проживания")
    fact_address_fias = models.CharField(max_length=128, blank=True, default=None, null=True, help_text="ФИАС Адрес факт. проживания")
    fact_address_details = JSONField(blank=True, null=True, help_text="Детали факт адреса")
    work_place = models.CharField(max_length=128, blank=True, default='', help_text="Место работы")
    work_place_db = models.ForeignKey('contracts.Company', blank=True, null=True, default=None, on_delete=models.SET_NULL, help_text="Место работы из базы")
    work_position = models.CharField(max_length=128, blank=True, default='', help_text="Должность")
    work_position_nsi_code = models.CharField(max_length=24, blank=True, null=True, default='', help_text="Код Должность НСИ")
    work_department = models.CharField(max_length=128, blank=True, default='', help_text="Подразделение")  # DEPRECATED
    work_department_db = models.ForeignKey('contracts.CompanyDepartment', blank=True, null=True, default=None, on_delete=models.SET_NULL, help_text="Место отдела из базы")
    mother = models.ForeignKey('self', related_name='mother_p', help_text="Мать", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    father = models.ForeignKey('self', related_name='father_p', help_text="Отец", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    curator = models.ForeignKey('self', related_name='curator_p', help_text="Опекун", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    curator_doc_auth = models.CharField(max_length=255, blank=True, default='', help_text="Документ-основание опекуна")
    agent = models.ForeignKey('self', related_name='agent_p', help_text="Представитель (из учреждения, родственник)", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    agent_doc_auth = models.CharField(max_length=255, blank=True, default='', help_text="Документ-основание представителя")
    payer = models.ForeignKey('self', related_name='payer_p', help_text="Плательщик", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    who_is_agent = models.CharField(max_length=7, choices=AGENT_CHOICES, blank=True, default='', help_text="Законный представитель пациента", db_index=True)
    district = models.ForeignKey(District, default=None, null=True, blank=True, help_text="Участок", on_delete=models.SET_NULL)
    ginekolog_district = models.ForeignKey(District, related_name='ginekolog_district', default=None, null=True, blank=True, help_text="Участок", on_delete=models.SET_NULL)

    anamnesis_of_life = models.TextField(default='', blank=True, help_text='Анамнез жизни')
    number_poliklinika = models.CharField(max_length=20, blank=True, default='', help_text="Идентификатор карты поликлиника", db_index=True)
    phone = models.CharField(max_length=20, blank=True, default='', db_index=True)
    harmful_factor = models.CharField(max_length=255, blank=True, default='', help_text="Фактор вредности")

    email = models.CharField(max_length=255, blank=True, default='')
    send_to_email = models.BooleanField(default=False, blank=True, db_index=True, help_text="Отправлять результаты на почту")

    medbook_prefix = models.CharField(max_length=3, blank=True, default='', db_index=True, help_text="Префикс номера мед.книжки")
    medbook_number = models.CharField(max_length=16, blank=True, default='', db_index=True, help_text="Номер мед.книжки")
    medbook_type = models.CharField(max_length=6, choices=MEDBOOK_TYPES, blank=True, default=MEDBOOK_TYPES[0][0], help_text="Тип номера мед.книжки")

    time_add = models.DateTimeField(default=timezone.now, null=True, blank=True)
    n3_id = models.CharField(max_length=40, help_text='N3_ID', blank=True, default="")
    death_date = models.DateField(help_text='Дата смерти', db_index=True, default=None, blank=True, null=True)
    contact_trust_health = models.CharField(max_length=400, help_text='Кому доверяю состояние здоровья', blank=True, default="")
    room_location = models.ForeignKey(Room, default=None, blank=True, null=True, help_text="Кабинет нахождения карты", db_index=True, on_delete=models.SET_NULL)

    owner = models.ForeignKey('hospitals.Hospitals', default=None, blank=True, null=True, help_text="Организация-владелец карты", db_index=True, on_delete=models.PROTECT)

    @property
    def main_address_full(self):
        return json.dumps({'address': self.main_address, 'fias': self.main_address_fias, 'details': self.main_address_details})

    @property
    def fact_address_full(self):
        return json.dumps({'address': self.fact_address, 'fias': self.fact_address_fias, 'details': self.fact_address_details})

    def __str__(self):
        return "{0} - {1}, {2}, Архив - {3}".format(self.number, self.base, self.individual, self.is_archive)

    def get_fio_w_card(self):
        return "{} №{} {} {}".format(get_system_name(), self.number, self.individual.fio(), self.individual.bd())

    def number_with_type(self):
        return "{}{}".format(self.number, (" " + self.base.short_title) if not self.base.is_rmis else "")

    def number_with_type_and_fio(self):
        return f"{self.number_with_type()} {self.individual.fio(short=False, full=True)}"

    def get_phones(self):
        return list(
            set([y for y in [x.normalize_number() for x in Phones.objects.filter(card__individual=self.individual, card__is_archive=False)] + [Phones.nn(self.phone)] if y and len(y) > 1])
        )

    def short_type_card(self):
        return "{}".format(self.base.short_title)

    def clear_phones(self, ts):
        to_delete = [x.pk for x in Phones.objects.filter(card=self) if x.number not in ts]
        Phones.objects.filter(pk__in=to_delete).delete()

    def add_phone(self, t: str):
        if not t:
            return
        t = t[:20]
        try:
            p, created = Phones.objects.get_or_create(card=self, number=t)
            p.normalize_number()
        except MultipleObjectsReturned:
            for p in Phones.objects.filter(card=self, number=t):
                p.normalize_number()

    def get_card_documents(self, as_model=False, check_has_type=None):
        if not check_has_type:
            types = [t.pk for t in DocumentType.objects.all()]
        else:
            types = [t.pk for t in DocumentType.objects.filter(title__in=check_has_type)]
        docs = {}
        for t in types:
            if not check_has_type:
                CardDocUsage.objects.filter(card=self, document__document_type__pk=t, document__is_active=False).delete()
            if CardDocUsage.objects.filter(card=self, document__document_type__pk=t, document__is_active=True).exists():
                if check_has_type:
                    return True
                docs[t] = CardDocUsage.objects.filter(card=self, document__document_type__pk=t)[0].document
            elif Document.objects.filter(document_type__pk=t, individual=self.individual, is_active=True).exists():
                d = Document.objects.filter(document_type__pk=t, individual=self.individual, is_active=True).order_by('-id')[0]
                c = CardDocUsage(card=self, document=d)
                c.save()
                docs[t] = d
                if check_has_type:
                    return True
            elif not check_has_type:
                docs[t] = None

            if not check_has_type and docs[t] and not as_model:
                docs[t] = docs[t].pk
        if check_has_type:
            return False
        return docs

    def get_n3_documents(self):
        docs = self.get_card_documents(as_model=True)

        result = []

        for t in DocumentType.objects.all():
            n3_t = t.n3_type

            if not n3_t or not docs.get(t.pk):
                continue

            doc: Document = docs[t.pk]
            d = {
                'number': doc.number,
                'series': doc.serial,
                'type': n3_t,
                'issuer': doc.who_give,
                'issuerId': '',
                'start': doc.date_start.strftime('%Y-%m-%d') if doc.date_start else None,
                'end': doc.date_end.strftime('%Y-%m-%d') if doc.date_end else None,
            }

            if n3_t == 'enp':
                ns = re.findall(r'\d{6}', d['issuer'])
                if ns:
                    d['issuerId'] = ns[0]
                else:
                    d['issuerId'] = '38014'

            result.append(d)

        return result

    def get_data_individual(self, empty=False, full_empty=False, only_json_serializable=False):
        if not empty and full_empty:
            empty = full_empty
        """
        Получает на входе объект Карта
        возвращает словарь атрибутов по карте и Физ.лицу(Индивидуалу)
        :param card_object:
        :return:
        """
        ind_data: Dict[Optional[Union[str, Dict, Individual]]] = {'ind': self.individual} if not full_empty else {}
        ind_data['age'] = self.individual.age()
        docs = []
        cd = self.get_card_documents()
        for d in cd:
            if d and Document.objects.filter(pk=cd[d]).exists():
                docs.append(Document.objects.filter(pk=cd[d])[0])
        ind_data['doc'] = docs if not full_empty else []
        ind_data['fio'] = self.individual.fio()
        ind_data['sex'] = self.individual.sex
        ind_data['family'] = self.individual.family
        ind_data['name'] = self.individual.name
        ind_data['patronymic'] = self.individual.patronymic
        ind_data['born'] = self.individual.bd()
        ind_data['birthday'] = self.individual.birthday
        ind_data['main_address'] = "____________________________________________________" if not self.main_address and not full_empty else self.main_address
        ind_data['fact_address'] = "____________________________________________________" if not self.fact_address and not full_empty else self.fact_address
        ind_data['card_num'] = self.number_with_type()
        ind_data['number_poliklinika'] = self.number_poliklinika
        ind_data['harmful_factor'] = self.harmful_factor
        ind_data['phone'] = self.get_phones()
        ind_data['work_place'] = self.work_place
        if not only_json_serializable:
            ind_data['work_place_db'] = self.work_place_db
        ind_data['work_position'] = self.work_position
        ind_data['work_department'] = self.work_department
        ind_data['sex'] = self.individual.sex

        # document "Паспорт РФ"
        ind_documents = Document.get_all_doc(docs)
        ind_data['passport_num'] = ind_documents['passport']['num']
        ind_data['passport_serial'] = ind_documents['passport']['serial']
        ind_data['passport_date_start'] = ind_documents['passport']['date_start']
        ind_data['passport_issued'] = (
            "______________________________________________________________" if not ind_documents['passport']['issued'] and not full_empty else ind_documents['passport']['issued']
        )
        ind_data['passport_issued_orig'] = ind_documents['passport']['issued']
        # document "св-во о рождении"
        ind_data['bc_num'] = ind_documents['bc']['num']
        ind_data['bc_serial'] = ind_documents['bc']['serial']
        ind_data['bc_date_start'] = ind_documents['bc']['date_start']
        ind_data['bc_issued'] = "______________________________________________________________" if not ind_documents['bc']['issued'] and not full_empty else ind_documents['bc']['issued']
        if ind_data['passport_num']:
            ind_data['type_doc'] = 'паспорт'
        elif ind_data['bc_num']:
            ind_data['type_doc'] = 'свидетельство о рождении'
        else:
            ind_data['type_doc'] = ''

        # document= "снилс'
        ind_data['snils'] = ind_documents["snils"]["num"].replace("-", "").replace(" ", "")
        # document= "полис ОМС"
        ind_data['oms'] = {}
        ind_data['oms']['polis_num'] = ind_documents["polis"]["num"]
        ind_data['oms']['number'] = ind_documents["polis"]["num"]
        ind_data['enp'] = ind_documents["polis"]["num"]
        if not ind_data['oms']['polis_num']:
            ind_data['oms']['polis_num'] = None if empty else '___________________________'
        ind_data['oms']['polis_serial'] = ind_documents["polis"]["serial"]
        if not ind_data['oms']['polis_serial']:
            ind_data['oms']['polis_serial'] = None if empty else '________'
        # ind_data['oms']['polis_date_start'] = ind_documents["polis"]["date_start"]
        ind_data['oms']['polis_issued'] = (None if empty else '') if not ind_documents["polis"]["issued"] else ind_documents["polis"]["issued"]
        ind_data['oms']['issueOrgName'] = '' if not ind_documents["polis"]["issued"] else ind_documents["polis"]["issued"]
        ind_data['insurer_full_code'] = '' if not ind_documents["polis"]["insurer_full_code"] else ind_documents["polis"]["insurer_full_code"]
        ind_data['oms']['issueOrgCode'] = ind_data['insurer_full_code']
        ind_data['ecp_id'] = self.individual.ecp_id

        patient_harmfull_factors = PatientHarmfullFactor.objects.filter(card=self)
        harmful_factors_title = [f"{i.harmful_factor.title}" for i in patient_harmfull_factors]
        ind_data['harmfull_factors'] = ";".join(harmful_factors_title)

        return ind_data

    def get_ecp_id(self):
        if self.individual.ecp_id:
            return self.individual.ecp_id
        else:
            individual_data = self.get_data_individual()
            from ecp_integration.integration import search_patient_ecp_by_fio

            ecp_id = search_patient_ecp_by_fio(individual_data)
            if ecp_id:
                self.individual.ecp_id = ecp_id
                self.individual.save()
                return self.individual.ecp_id
        return None

    @staticmethod
    def next_l2_n():
        last_l2 = Card.objects.filter(base__internal_type=True, number__regex=r'^\d+$').extra(select={'numberInt': 'CAST(number AS INTEGER)'}).order_by("-numberInt").first()
        n = 0
        if last_l2:
            n = last_l2.numberInt
        return n + 1

    @staticmethod
    def next_medbook_n():
        last_medbook = Card.objects.filter(base__internal_type=True).exclude(medbook_number='').extra(select={'numberInt': 'CAST(medbook_number AS INTEGER)'}).order_by("-numberInt").first()
        n = 0
        if last_medbook:
            n = last_medbook.numberInt
        return max(n + 1, SettingManager.get_medbook_auto_start())

    @staticmethod
    def add_l2_card(
        individual: Union[Individual, None] = None,
        card_orig: Union['Card', None] = None,
        distinct=True,
        polis: Union['Document', None] = None,
        address: Union[str, None] = None,
        force=False,
        updated_data=None,
        snils: Union['Document', None] = None,
        owner=None,
        email=email,
        phone=phone,
    ):
        f = {'owner': owner} if owner else {}
        if distinct and card_orig and Card.objects.filter(individual=card_orig.individual if not force else (individual or card_orig.individual), base__internal_type=True, **f).exists():
            return None

        if force and Card.objects.filter(individual=card_orig.individual if not force else (individual or card_orig.individual), base__internal_type=True, **f).exists():
            c = Card.objects.filter(individual=card_orig.individual if not force else (individual or card_orig.individual), base__internal_type=True, **f)[0]
            updated = []

            if address and c.main_address != address:
                c.main_address = address
                updated.append('main_address')
                if updated_data:
                    updated_data.append('Адрес регистрации')

            if polis and c.polis != polis:
                c.polis = polis
                updated.append('polis')
                if updated_data:
                    updated_data.append('Основной полис')

            if updated:
                print('Updated:', updated)  # noqa: T001
                c.save(update_fields=updated)

            if polis:
                cdu = CardDocUsage.objects.filter(card=c, document__document_type=polis.document_type)
                if not cdu.exists():
                    CardDocUsage(card=c, document=polis).save()
                else:
                    for cd in cdu:
                        cd.document = polis
                        cd.save(update_fields=["document"])

            return c

        with transaction.atomic():
            cb = list(CardBase.objects.filter(internal_type=True).select_for_update())
            if (not card_orig and not individual) or not cb:
                return
            c = Card(
                number=Card.next_l2_n(),
                base=cb[0],
                individual=individual if individual else card_orig.individual,
                polis=polis or (None if not card_orig else card_orig.polis),
                main_diagnosis='' if not card_orig else card_orig.main_diagnosis,
                main_address=address or ('' if not card_orig else card_orig.main_address),
                fact_address='' if not card_orig else card_orig.fact_address,
                phone=phone,
                email=email,
                **f,
            )
            c.save()
            if polis:
                CardDocUsage(card=c, document=polis).save()
            if snils:
                CardDocUsage(card=c, document=snils).save()
            print('Created card')  # noqa: T001
            return c

    class Meta:
        verbose_name = 'Карта'
        verbose_name_plural = 'Карты'


def on_obj_pre_save_log(sender, instance: Union[Document, CardDocUsage, Card, Individual], **kwargs):  # NOQA
    if not isinstance(instance, (Card, Document, CardDocUsage, Individual)):
        return
    try:
        for frame_record in inspect.stack():
            if frame_record[3] == 'get_response':
                request = frame_record[0].f_locals['request']
                break
        else:
            request = None

        doctorprofile = request.user.doctorprofile if request and hasattr(request.user, 'doctorprofile') and request.user.is_authenticated else None

        if instance.pk is not None:
            orig = sender.objects.get(pk=instance.pk)
            field_names = [field.name for field in sender._meta.fields]
            updated_data = {}
            for field_name in field_names:
                help_text = sender._meta.get_field(field_name).help_text

                if not help_text or field_name == 'pk':
                    continue

                from_value = getattr(orig, field_name)
                from_value = from_value if from_value is None or isinstance(from_value, (str, bool, int, float)) else str(from_value)
                to_value = getattr(instance, field_name)
                to_value = to_value if to_value is None or isinstance(to_value, (str, bool, int, float)) else str(to_value)

                if from_value != to_value:
                    updated_data[field_name] = {
                        "from": from_value,
                        "to": to_value,
                        "help_text": str(help_text),
                        "field_name": field_name,
                    }
            if not updated_data:
                return
            k = 30007
            if isinstance(instance, Document):
                k = 30008
            elif isinstance(instance, CardDocUsage):
                k = 30009
            elif isinstance(instance, Individual):
                k = 30010
            slog.Log.log(instance.pk, k, doctorprofile, {"updates": list(updated_data.values())})
    except Exception as e:
        print(e)  # noqa: T001
        logger.exception(e)


pre_save.connect(on_obj_pre_save_log, sender=Document)
pre_save.connect(on_obj_pre_save_log, sender=CardDocUsage)
pre_save.connect(on_obj_pre_save_log, sender=Card)
pre_save.connect(on_obj_pre_save_log, sender=Individual)


class AnamnesisHistory(models.Model):
    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    text = models.TextField(help_text='Анамнез жизни')
    who_save = models.ForeignKey('users.DoctorProfile', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def created_at_local(self):
        return localtime(self.created_at)


class DispensaryReg(models.Model):
    TIMES = (
        (0, 'не указано'),
        (1, 'впервые'),
        (2, 'повторно'),
    )

    IDENTIFIEDS = (
        (0, 'не указано'),
        (1, 'обращении за лечением'),
        (2, 'профилактическом осмотре'),
    )

    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    diagnos = models.CharField(max_length=511, help_text='Диагноз Д-учета', default='', blank=True, db_index=True)
    illnes = models.CharField(max_length=511, help_text='Заболевание по которому состоит на учете', default='', blank=True)
    spec_reg = models.ForeignKey(Speciality, related_name='doc_spec_start', default=None, blank=True, null=True, help_text="Профиль специальности", db_index=True, on_delete=models.CASCADE)
    doc_start_reg = models.ForeignKey(
        DoctorProfile, related_name='doc_start_reg', default=None, blank=True, null=True, db_index=True, help_text='Лечащий врач кто поставил на учет', on_delete=models.CASCADE
    )
    date_start = models.DateField(help_text='Дата постановки на Д-учет', db_index=True, default=None, blank=True, null=True)
    doc_end_reg = models.ForeignKey(
        DoctorProfile, related_name='doc_end_reg', default=None, blank=True, null=True, db_index=True, help_text='Лечащий врач, кто снял с учета', on_delete=models.CASCADE
    )
    date_end = models.DateField(help_text='Дата сняти с Д-учета', db_index=True, default=None, blank=True, null=True)
    why_stop = models.CharField(max_length=511, help_text='Причина снятия с Д-учета', default='', blank=True)
    what_times = models.SmallIntegerField(choices=TIMES, default=0, help_text="Как установлен диагноз")
    how_identified = models.SmallIntegerField(choices=IDENTIFIEDS, default=0, help_text="как установлен диагноз")
    is_additional = models.BooleanField(help_text="Дополнение к пациенту", default=False)

    class Meta:
        verbose_name = 'Д-учет'
        verbose_name_plural = 'Д-учет'


class PatientHarmfullFactor(models.Model):
    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    harmful_factor = models.ForeignKey(HarmfulFactor, default=None, blank=True, null=True, db_index=True, help_text='Фактор вредности', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Фактор вредности у пациента'
        verbose_name_plural = 'Факторы вредности пациентов'

    @staticmethod
    def get_card_harmful_factor(card):
        patient_harmful_factors = PatientHarmfullFactor.objects.filter(card=card)
        return [{"factorId": p.harmful_factor.pk} for p in patient_harmful_factors]

    @staticmethod
    def save_card_harmful_factor(card_pk, tb_data):
        card = Card.objects.filter(pk=card_pk).first()
        PatientHarmfullFactor.objects.filter(card=card).delete()
        for t_b in tb_data:
            harmfull = HarmfulFactor.objects.filter(pk=t_b['factorId']).first()
            if harmfull:
                PatientHarmfullFactor(card=card, harmful_factor=harmfull).save()

        return True


class AdditionalPatientDispensaryPlan(models.Model):
    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    research = models.ForeignKey(Researches, db_index=True, blank=True, default=None, null=True, help_text='Исследование включенное в список', on_delete=models.CASCADE)
    repeat = models.PositiveSmallIntegerField(db_index=True, help_text='Кол-во в год', null=False, blank=False)
    diagnos = models.CharField(max_length=511, help_text='Диагноз Д-учета', default='', blank=True, db_index=True)
    speciality = models.ForeignKey(Speciality, db_index=True, blank=True, default=None, null=True, help_text='Профиль-специальности консультации врача', on_delete=models.CASCADE)
    is_visit = models.BooleanField(default=False, blank=True, db_index=True)

    class Meta:
        verbose_name = 'Индивидуальное дополнение к диспансерному учету'
        verbose_name_plural = 'Индивидуальные дополнение к диспансерному учету'


class DispensaryRegPlans(models.Model):
    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    research = models.ForeignKey(Researches, db_index=True, blank=True, default=None, null=True, help_text='Исследование включенное в список', on_delete=models.CASCADE)
    speciality = models.ForeignKey(Speciality, db_index=True, blank=True, default=None, null=True, help_text='Профиль-специальности консультации врача', on_delete=models.CASCADE)
    date = models.DateField(help_text='Планируемая дата', db_index=True, default=None, blank=True, null=True)

    class Meta:
        verbose_name = 'Д-учет план'
        verbose_name_plural = 'Д-учет план'

    @staticmethod
    def update_plan(card_pk, old_research, new_research, year):
        card = Card.objects.get(pk=card_pk)
        for i in range(len(old_research)):
            research_pk, speciality_pk = None, None
            type_research = old_research[i]["type"]
            if type_research == "research":
                research_pk = old_research[i]["research_pk"]
            elif type_research == "speciality":
                speciality_pk = old_research[i]["research_pk"]
            old_plans = old_research[i]["plans"]
            new_plans = [''.join(c for c in x if c.isdigit()) for x in new_research[i]["plans"]]
            for m in range(12):
                if old_plans[m] != new_plans[m]:
                    try:
                        if old_plans[m]:
                            current_date = f'{year}-{m + 1}-{old_plans[m]}'
                            old_data_plan = DispensaryRegPlans.objects.filter(card=card, research__pk=research_pk, speciality__pk=speciality_pk, date=current_date).first()
                        else:
                            old_data_plan = DispensaryRegPlans.objects.filter(card=card, research__pk=research_pk, speciality__pk=speciality_pk, date__isnull=True).first()
                        if old_data_plan:
                            if new_plans[m]:
                                new_date = f'{year}-{m + 1}-{new_plans[m]}'
                                old_data_plan.date = new_date
                                old_data_plan.save()
                            else:
                                old_data_plan.delete()
                        else:
                            DispensaryRegPlans.objects.create(card=card, research_id=research_pk, speciality_id=speciality_pk, date=f'{year}-{m + 1}-{new_plans[m]}')
                    except Exception as e:
                        # Возможно косячные даты с фронтенда вроде "99" или "абв", временное решение просто проигнорить
                        print(e)  # noqa: T001


class ScreeningRegPlan(models.Model):
    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    research = models.ForeignKey(Researches, db_index=True, help_text='Исследование', on_delete=models.CASCADE)
    date = models.DateField(help_text='Планируемая дата', db_index=True)
    ages = ArrayField(models.PositiveSmallIntegerField(default=[], blank=True, help_text='Возраст(лет) во время к-рых необходимо выполнить обследование'))

    def __str__(self):
        return f"{self.card} – {self.research}, {strfdatetime(self.date, '%d-%m-%Y')}"

    class Meta:
        unique_together = ("card", "research", "ages")

        verbose_name = 'Скрининг план'
        verbose_name_plural = 'Скрининг план'

    @staticmethod
    def get_screening_data(card_pk):
        client_obj = Card.objects.get(pk=card_pk)
        sex_client = client_obj.individual.sex
        age_patient = client_obj.individual.age_for_year()
        year = 6
        now_year = int(current_year())
        all_years_patient = [i for i in range(now_year - year, now_year + year + 1)]
        all_ages_patient = [i for i in range(age_patient - year, age_patient + year + 1)]
        screening_plan_obj = ScreeningPlan.objects.filter(
            Q(age_start_control__lte=age_patient, age_end_control__gte=age_patient, hide=False), Q(sex_client=sex_client) | Q(sex_client='в')
        ).order_by('sort_weight')

        ages_years = {}
        for i in range(len(all_years_patient)):
            ages_years[all_ages_patient[i]] = all_years_patient[i]

        researches = []
        researches_pks = []
        for screening_plan in screening_plan_obj:
            period = screening_plan.period
            start_age_control = screening_plan.age_start_control
            end_age_control = screening_plan.age_end_control
            all_ages_research = [i for i in range(start_age_control, screening_plan.age_end_control + 1)]

            ages_patient_research = []
            for k in range(len(all_ages_patient)):
                if all_ages_patient[k] in all_ages_research:
                    ages_patient_research.append(all_ages_patient[k])
                else:
                    ages_patient_research.append(None)

            count_slice = math.ceil(len(all_ages_research) / period)

            slice_ages = {}
            start = 0
            for c in range(count_slice):
                for k in range(period):
                    if start < len(all_ages_research):
                        slice_ages[all_ages_research[start]] = c
                        start += 1
                    else:
                        break

            ages_research = []
            temp_ages = {"isEven": False, "plan": None, "planYear": None, "values": []}
            count = 0
            old_part_slice = None
            ages_plan = []
            for j in range(len(all_ages_patient)):
                ap = all_ages_patient[j]
                a_patient = None if j >= len(ages_patient_research) else ages_patient_research[j]
                if not a_patient:
                    temp_ages["values"].append(None)
                    continue

                new_part_slice = slice_ages.get(ap, None)
                if count == 0:
                    old_part_slice = new_part_slice

                if slice_ages.get(ap, -1) > -1 and new_part_slice == old_part_slice:
                    temp_ages["values"].append({"age": ap, "year": ages_years[ap], "fact": None})
                    ages_plan.append(ap)

                if new_part_slice != old_part_slice:
                    temp_ages["isEven"] = old_part_slice is not None and old_part_slice % 2 == 0
                    plan_obj = ScreeningRegPlan.objects.filter(card_id=client_obj, research_id=screening_plan.research.pk, ages=ages_plan)
                    if plan_obj.exists():
                        if len(plan_obj) > 0:
                            plan_date = strfdatetime(plan_obj[0].date, '%d.%m.%Y')
                            temp_ages["plan"] = plan_date
                            temp_ages["planYear"] = int(strfdatetime(plan_obj[0].date, '%Y'))
                    ages_research.append(temp_ages)
                    temp_ages = {"isEven": None, "plan": None, "planYear": None, "values": []}
                    ages_plan = []
                    if slice_ages.get(ap):
                        temp_ages["values"].append({"age": ap, "year": ages_years[ap], "fact": None})
                        ages_plan.append(ap)
                count += 1
                old_part_slice = new_part_slice

            temp_ages["isEven"] = old_part_slice is not None and old_part_slice % 2 == 0
            plan_obj = ScreeningRegPlan.objects.filter(card_id=client_obj, research_id=screening_plan.research.pk, ages=ages_plan)
            if plan_obj.exists():
                if len(plan_obj) > 0:
                    plan_date = strfdatetime(plan_obj[0].date, '%d.%m.%Y')
                    temp_ages["plan"] = plan_date
                    temp_ages["planYear"] = int(strfdatetime(plan_obj[0].date, '%Y'))

            ages_research.append(temp_ages)

            researches.append(
                {
                    "pk": screening_plan.research.pk,
                    "title": screening_plan.research.title,
                    "startAgeControl": start_age_control,
                    "endAgeControl": end_age_control,
                    "period": period,
                    "ages": ages_research,
                }
            )
            researches_pks.append(screening_plan.research.pk)
        screening = {"patientAge": age_patient, "currentYear": now_year, "years": all_years_patient, "ages": all_ages_patient, "researches": researches}
        last_years_result = last_result_researches_years(card_pk, all_years_patient, researches_pks)

        results_research = {}
        for i in last_years_result:
            if not results_research.get(i.research_id):
                results_research[i.research_id] = {}
            if not results_research[i.research_id].get(int(i.year_date)):
                results_research[i.research_id][int(i.year_date)] = {}

            month = f'{int(i.month_date):02}'
            day = f'{int(i.day_date):02}'
            results_research[i.research_id][int(i.year_date)] = {'day': day, 'month': month, 'direction': i.dir_id}

        for i in screening["researches"]:
            if not results_research.get(i["pk"]):
                continue
            research_fact_result = results_research.get(i["pk"])
            for age in i['ages']:
                for v in age['values']:
                    if not v or not research_fact_result.get(v['year']):
                        continue
                    else:
                        data_fact = research_fact_result.get(v['year'])
                    day = data_fact.get("day")
                    month = data_fact.get("month")
                    direction = data_fact.get("direction")
                    v['fact'] = {"date": f'{day}.{month}', "direction": direction}

        return screening

    @staticmethod
    def update_plan(data):
        ages = [age_data['age'] for age_data in data['ageGroup']['values']]
        plan = data['ageGroup']['plan']
        plan_date = None
        if plan:
            plan_date = datetime.strptime(plan, "%d.%m.%Y").date()

        plan_screening_obj = ScreeningRegPlan.objects.filter(card_id=data['cardPk'], research_id=data['researchPk'], ages=ages)
        if plan_screening_obj.exists():
            if len(plan_screening_obj) > 1:
                return {"messge": "Ошибка с возрастами! Проверьте настройки"}
            else:
                if not plan_date:
                    plan_screening_obj[0].delete()
                else:
                    plan_screening_obj[0].date = plan_date
                    plan_screening_obj[0].save()
        else:
            ScreeningRegPlan(card_id=data['cardPk'], research_id=data['researchPk'], ages=ages, date=plan_date).save()


class Phones(models.Model):
    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    number = models.CharField(max_length=20, help_text='Номер телефона', db_index=True)
    normalized_number = models.CharField(max_length=20, blank=True, default='', help_text='(NORMALIZED) Номер телефона', db_index=True)

    def normalize_number(self):
        n = self.nn(self.number)
        if self.normalized_number != n:
            self.normalized_number = n
            self.save()
        return n

    @staticmethod
    def phones_to_normalized_list(phones: List['Phones'], more_phone=''):
        return list(set([y for y in [x.normalize_number() for x in phones] + [Phones.nn(more_phone)] if y and len(y) > 1]))

    @staticmethod
    def nn(n):
        n = n.replace("+7", "8")
        n = ''.join(c for c in n if c in '0123456789')
        if len(n) == 10 and n[0] == "9":
            n = "8" + n
        if len(n) == 11 and n[0] == "7":
            n = "8" + n[1:]
        return n

    @staticmethod
    def format_as_plus_7(n):
        phone = Phones.nn(n)
        if len(phone) != 11:
            return phone[:11]
        return f"+7 {phone[1:4]} {phone[4:7]}-{phone[7:9]}-{phone[9:]}"

    @staticmethod
    def normalize_to_search(n):
        nn = Phones.nn(n)

        r = [
            n,
            nn,
        ]

        if len(nn) == 11:
            r.append(f"{nn[0]} {nn[1:4]} {nn[4:]}")

        return r

    def __str__(self):
        return "{0}: {1}".format(self.card, self.number)

    class Meta:
        verbose_name = 'Телефон'
        verbose_name_plural = 'Телефоны'


class BenefitType(models.Model):
    TYPES = (
        (0, ''),
        (1, 'Федеральная'),
        (2, 'Региональная'),
        (3, 'Муниципальная'),
        (4, 'ВЗН'),
    )

    title = models.CharField(max_length=255, help_text='Категория льготы')
    hide = models.BooleanField(help_text="Скрыть категорию", default=False)
    field_type = models.SmallIntegerField(default=0, choices=TYPES, blank=True)

    def __str__(self):
        return "{} – {}".format(self.get_field_type_display(), self.title)

    class Meta:
        verbose_name = 'Категория льготы'
        verbose_name_plural = 'Категории льготы'


class BenefitReg(models.Model):
    """
    Учет пациентов по льготам, стоящим на текущий момент
    """

    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    benefit = models.ForeignKey(BenefitType, related_name='benefit', help_text="Льгота", db_index=True, on_delete=models.CASCADE)
    doc_start_reg = models.ForeignKey(
        DoctorProfile, related_name='doc_start_benefit', default=None, blank=True, null=True, db_index=True, help_text='Лечащий врач кто поставил на льготу', on_delete=models.CASCADE
    )
    date_start = models.DateField(help_text='Дата постановки на Льготу', db_index=True, default=None, blank=True, null=True)
    doc_end_reg = models.ForeignKey(
        DoctorProfile, related_name='doc_end_benefit', default=None, blank=True, null=True, db_index=True, help_text='Лечащий врач, кто снял с льготы', on_delete=models.CASCADE
    )
    date_end = models.DateField(help_text='Дата сняти с льготы', db_index=True, default=None, blank=True, null=True)
    registration_basis = models.TextField(default="", blank=True)


class VaccineReg(models.Model):
    STEPS = (
        'V',
        'V1',
        'V2',
        'V3',
        'V4',
        'R',
        'R1',
        'R2',
        'R3',
    )
    STEPS_CHOICES = (
        (
            x,
            x,
        )
        for x in STEPS
    )

    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    date = models.DateField(help_text='Дата', db_index=True, null=True, default=None, blank=True)
    direction = models.CharField(max_length=20, help_text='Направление', db_index=True, default='', blank=True)
    title = models.CharField(max_length=255, help_text='Название', db_index=True, default='', blank=True)
    series = models.CharField(max_length=255, help_text='Серия', db_index=True, default='', blank=True)
    amount = models.CharField(max_length=127, help_text='Доза', db_index=True, default='', blank=True)
    method = models.CharField(max_length=127, help_text='Способ', db_index=True, default='', blank=True)
    step = models.CharField(max_length=20, help_text='Этап', db_index=True, choices=STEPS_CHOICES, default='V', blank=True)
    tap = models.CharField(max_length=20, help_text='Отвод', db_index=True, default='', blank=True)
    comment = models.TextField(help_text='Примечание', default='', blank=True)
    doc = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, help_text='Кто создал запись', on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Д-учет'
        verbose_name_plural = 'Д-учет'


class AmbulatoryData(models.Model):
    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    date = models.DateField(help_text='Дата', db_index=True, null=True, default=None, blank=True)
    data = models.TextField(default='', blank=True, help_text='Сведения из амбулаторной карты')
    doc = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, help_text='Кто создал запись', on_delete=models.SET_NULL)


class AmbulatoryDataHistory(models.Model):
    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    text = models.TextField(help_text='Анамнез жизни')
    who_save = models.ForeignKey('users.DoctorProfile', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def created_at_local(self):
        return localtime(self.created_at)

    @staticmethod
    def save_ambulatory_history(card_pk, doc):
        ambulatory_data = AmbulatoryData.objects.filter(card__pk=card_pk).order_by('date')
        data = ''
        for i in ambulatory_data:
            data = f"{data} {str(i.date)[0:7]}: {i.data};"
        a = AmbulatoryDataHistory.objects.create(card_id=card_pk)
        a.text = data
        a.who_save = doc
        a.save()


class CardControlParam(models.Model):
    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    patient_control_param = models.ForeignKey(PatientControlParam, default=None, null=True, blank=True, help_text='Контролируемый параметр', on_delete=models.SET_NULL)
    purpose_value = models.CharField(max_length=50, help_text='Целевое значение-нормальност', default="")
    date_start = models.DateField(help_text='Дата начала контроля', default=None, blank=True, null=True)
    date_end = models.DateField(help_text='Дата окончания контроля', default=None, blank=True, null=True)

    def __str__(self):
        return f"{self.patient_control_param} - {self.purpose_value}"

    class Meta:
        verbose_name = 'Контролируемый параметр у пациента'
        verbose_name_plural = 'Контролируемые параметры у пациента'

    @staticmethod
    def get_patient_control_param(card_pk, code_param_id=None):
        card_controls = CardControlParam.objects.filter(card_id=card_pk).order_by("pk")
        if code_param_id:
            card_controls = CardControlParam.objects.filter(card_id=card_pk, patient_control_param_id=code_param_id).order_by("pk")
        control_params = {cc.patient_control_param_id: {"title": cc.patient_control_param.title, "purpose": "", "selected": True, "isGlobal": False} for cc in card_controls}
        for cc in card_controls:
            tmp_data: dict = control_params[cc.patient_control_param_id]
            date_start = cc.date_start.strftime("%m.%y") if cc.date_start else "-"
            date_end = cc.date_end.strftime("%m.%y") if cc.date_end else "-"
            tmp_purpose = f"{tmp_data['purpose']} {date_start}:{date_end}={cc.purpose_value};"
            tmp_data["purpose"] = tmp_purpose
            control_params[cc.patient_control_param_id] = tmp_data.copy()
        all_patient_contol_param = PatientControlParam.get_all_patient_contol_param(code_param_id=code_param_id)
        for k, v in all_patient_contol_param.items():
            if not control_params.get(k, None):
                control_params[k] = v
                control_params[k]["selected"] = True
                control_params[k]["isGlobal"] = True
            if control_params.get(k, None):
                control_params[k]["isGlobal"] = True
        return control_params

    @staticmethod
    def save_patient_control_param(card_pk, save_params):
        CardControlParam.objects.filter(card_id=card_pk).order_by("pk").delete()
        for i in save_params:
            if i.get("isGlobal", False):
                continue
            elif i.get("isSelected", False):
                CardControlParam(card_id=card_pk, patient_control_param_id=i["id"]).save()


class CardMovementRoom(models.Model):
    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    room_out = models.ForeignKey(Room, help_text="Кабинет откуда", related_name="room_out", default=None, blank=True, null=True, db_index=True, on_delete=models.CASCADE)
    room_in = models.ForeignKey(Room, help_text="Кабинет куда ", default=None, blank=True, null=True, related_name="room_in", db_index=True, on_delete=models.CASCADE)
    doc_who_issued = models.ForeignKey(DoctorProfile, related_name="doc_who_issued", default=None, blank=True, null=True, help_text='Отправитель', on_delete=models.SET_NULL)
    date_issued = models.DateTimeField(auto_now_add=True, help_text='Дата выдачи карт', db_index=True)
    doc_who_received = models.ForeignKey(DoctorProfile, related_name="doc_who_received", default=None, blank=True, null=True, help_text='Приемщик', on_delete=models.SET_NULL)
    date_received = models.DateTimeField(default=None, blank=True, null=True, help_text='Дата подтверждения получения', db_index=True)
    comment = models.CharField(max_length=128, help_text='Комментарий движения', default="")

    @staticmethod
    def transfer_send(cards, room_out_id, room_in_id, doc_who_issued_id):
        for i in cards:
            CardMovementRoom(card_id=i['id'], room_out_id=room_out_id, room_in_id=room_in_id, doc_who_issued_id=doc_who_issued_id).save()
            card = Card.objects.filter(id=i['id']).first()
            card.room_location_id = room_in_id
            card.save()
        return True

    @staticmethod
    def transfer_accept(cards, room_out_id, room_in_id, doc_who_received_id):
        for i in cards:
            transfer_card = CardMovementRoom.objects.filter(card_id=i['id'], room_out_id=room_out_id, room_in_id=room_in_id, doc_who_received_id=None).first()
            transfer_card.doc_who_received_id = doc_who_received_id
            today = datetime.now().date()
            transfer_card.date_received = today
            transfer_card.save()
        return True

    @staticmethod
    def get_await_accept(room_in_ids):
        card_objs = CardMovementRoom.objects.filter(room_in_id__in=room_in_ids)
        rooms_out = []
        rooms_out_result = []
        for i in card_objs:
            if i.room_out.id not in rooms_out:
                rooms_out_result.append({"id": i.room_out.id, "label": i.room_out.title})
                rooms_out.append(i.room_out.id)
        return rooms_out_result

    @staticmethod
    def get_accept_card(
        room_out_id,
        room_in_id,
    ):
        card_ids = CardMovementRoom.objects.values_list("card_id", flat=True).filter(room_in_id=room_in_id, room_out_id=room_out_id, date_received=None, doc_who_received=None)
        return Card.objects.filter(id__in=card_ids)
