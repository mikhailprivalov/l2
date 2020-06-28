import sys
from datetime import date, datetime
from typing import List

import simplejson
from dateutil.relativedelta import relativedelta
from django.core.management.base import OutputWrapper
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

import slog.models as slog
from appconf.manager import SettingManager
from laboratory.utils import localtime, current_year, strfdatetime
from users.models import Speciality, DoctorProfile

TESTING = 'test' in sys.argv[1:] or 'jenkins' in sys.argv[1:]


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
    tfoms_idp = models.CharField(max_length=64, default=None, null=True, blank=True)
    time_tfoms_last_sync = models.DateTimeField(default=None, null=True, blank=True)

    time_add = models.DateTimeField(default=timezone.now, null=True, blank=True)

    def join_individual(self, b: 'Individual', out: OutputWrapper = None):
        if out:
            out.write("Карт для переноса: %s" % Card.objects.filter(individual=b).count())
        slog.Log(key=str(self.pk), type=2002,
                 body=simplejson.dumps({"Сохраняемая запись": str(self), "Объединяемая запись": str(b)}),
                 user=None).save()
        for c in Card.objects.filter(individual=b):
            c.individual = self
            c.save()
        b.delete()

    def sync_with_rmis(self, out: OutputWrapper = None, c=None):
        if not SettingManager.get("rmis_enabled", default='false', default_type='b') or not CardBase.objects.filter(is_rmis=True).exists():
            return
        if self.primary_for_rmis:
            self.reverse_sync()
            return
        if out:
            out.write("Обновление данных для: %s" % self.fio(full=True))
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

        if not ok:
            docs = Document.objects.filter(individual=self).exclude(document_type__check_priority=0).order_by(
                "-document_type__check_priority")
            for document in docs:
                s = c.patients.search_by_document(document)
                if len(s) > 0:
                    rmis_uid = s[0]
                    ok = True
                    if out:
                        out.write("Физ.лицо найдено по документу: %s -> %s" % (document, rmis_uid))
                    break

        if ok:
            data = c.patients.get_data(rmis_uid)
            upd = self.family != data["family"] or self.name != data["name"] or self.patronymic != data[
                "patronymic"] or (self.birthday != data["birthday"] and data["birthday"] is not None)

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
                slog.Log(key=str(self.pk), type=2003,
                         body=simplejson.dumps({"Новые данные": str(self), "Не актуальные данные": prev}),
                         user=None).save()

        if not ok:
            query = {"surname": self.family, "name": self.name, "patrName": self.patronymic,
                     "birthDate": self.birthday.strftime("%Y-%m-%d")}
            rows = c.patients.client.searchIndividual(**query)
            if len(rows) == 1:
                rmis_uid = rows[0]
                ok = True
                if out:
                    out.write("Физ.лицо найдено по ФИО и д.р.: %s" % rmis_uid)

        if not has_rmis and rmis_uid and rmis_uid != '':
            ex = Card.objects.filter(number=rmis_uid, is_archive=False, base__is_rmis=True)
            if ex.exists():
                for e in ex:
                    self.join_individual(e.individual, out)
            s = str(c.patients.create_rmis_card(self, rmis_uid))
            if out:
                out.write("Добавление РМИС карты -> %s" % s)

        save_docs = []

        if ok and rmis_uid != "" and Card.objects.filter(individual=self, base__is_rmis=True,
                                                         is_archive=False).exists():
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
                    data = dict(document_type=DocumentType.objects.get(pk=k),
                                serial=document_object["series"] or "",
                                number=document_object["number"] or "",
                                date_start=document_object["issueDate"],
                                date_end=document_object["expiryDate"],
                                who_give=(document_object["issueOrganization"] or {"name": document_object["issuerText"] or ""})["name"] or "",
                                individual=self,
                                is_active=True)
                    rowss = Document.objects.filter(document_type=data['document_type'], individual=self,
                                                    from_rmis=True)
                    if rowss.exclude(serial=data["serial"]).exclude(number=data["number"]).filter(card__isnull=True).exists():
                        Document.objects.filter(document_type=data['document_type'], individual=self,
                                                from_rmis=True).delete()
                    docs = Document.objects.filter(document_type=data['document_type'],
                                                   serial=data['serial'],
                                                   number=data['number'], from_rmis=True)
                    if not docs.exists():
                        doc = Document(**data)
                        doc.save()
                        if out:
                            out.write("Добавление докумена: %s" % doc)
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
                        docs = Document.objects.filter(document_type=data['document_type'],
                                                       serial=data['serial'],
                                                       number=data['number'],
                                                       individual=self)
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

                    docs = Document.objects.filter(document_type=data['document_type'],
                                                   document_type__title__in=['СНИЛС', 'Паспорт гражданина РФ',
                                                                             'Полис ОМС'],
                                                   serial=data['serial'],
                                                   number=data['number']).exclude(individual=self).exclude(number="")
                    if docs.exists():
                        if out:
                            out.write("Объединение записей физ.лиц")
                        for doc in docs:
                            self.join_individual(doc.individual, out)

            to_delete_pks = []
            for d in Document.objects.filter(individual=self, from_rmis=True):
                kk = "%s_%s_%s" % (d.document_type_id, d.serial, d.number)
                if out:
                    out.write("TD %s %s %s" % (kk, kk not in save_docs, save_docs,))
                if kk not in save_docs:
                    to_delete_pks.append(d.pk)
            Document.objects.filter(pk__in=to_delete_pks).delete()
        else:
            self.primary_for_rmis = True
            self.save()
            self.reverse_sync()
            if out:
                out.write("Физ.лицо не найдено в РМИС")
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
            if self.family != p["lastName"] or \
                    self.name != p["firstName"] or \
                    self.patronymic != p["middleName"] or \
                    self.sex != g or \
                    self.birthday != self.birthday:
                c.patients.edit_patient(self)

    def bd(self):
        return "{:%d.%m.%Y}".format(self.birthday)

    # подсчет возраста в рамках года
    def age_for_year(self):
        year_today = current_year()
        last_date = datetime.strptime(f'31.12.{year_today}', '%d.%m.%Y').date()
        born_date = self.birthday
        return last_date.year - born_date.year - ((last_date.month, last_date.day) < (born_date.month, born_date.day))

    def age(self, iss=None, days_monthes_years=False):
        """
        Функция подсчета возраста
        """

        if iss is None or (not iss.tubes.exists() and not iss.time_confirmation) or \
            ((not iss.tubes.exists() or not iss.tubes.filter(
                time_recive__isnull=False).exists()) and not iss.research.is_paraclinic and not iss.research.is_doc_refferal):
            today = date.today()
        elif iss.time_confirmation and (iss.research.is_paraclinic or iss.research.is_doc_refferal) or not iss.tubes.exists():
            today = iss.time_confirmation.date()
        else:
            today = iss.tubes.filter(time_recive__isnull=False).order_by("-time_recive")[0].time_recive.date()
        born = self.birthday
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
            i = Issledovaniya.objects.filter(tubes__time_recive__isnull=False, napravleniye=direction) \
                .order_by("-tubes__time_recive")
            if i.exists():
                iss = i[0]
            elif Issledovaniya.objects.filter(research__is_paraclinic=True, napravleniye=direction,
                                              time_confirmation__isnull=False):
                iss = Issledovaniya.objects.filter(research__is_paraclinic=True, napravleniye=direction,
                                                   time_confirmation__isnull=False) \
                    .order_by("-time_confirmation")[0]

        days, monthes, years = self.age(iss=iss, days_monthes_years=True)

        if years > 0:
            age = years
            ages = AgeCache.objects.filter(n=age, t=0)
            if ages.exists():
                r = ages[0].s
            else:
                import pymorphy2
                morph = pymorphy2.MorphAnalyzer()
                if age == 0:
                    _let = morph.parse("лет ")[0]
                elif age < 5:
                    _let = morph.parse("год")[0]
                elif age <= 20:
                    _let = morph.parse("лет ")[0]
                elif 5 > age % 10 > 0:
                    _let = morph.parse("год")[0]
                else:
                    _let = morph.parse("лет ")[0]
                r = "{0} {1}".format(age, _let.make_agree_with_number(age).word).strip()
                AgeCache(n=age, t=0, s=r).save()
        elif monthes > 0:
            age = monthes
            ages = AgeCache.objects.filter(n=age, t=1)

            if ages.exists():
                r = ages[0].s
            else:
                import pymorphy2
                morph = pymorphy2.MorphAnalyzer()
                if age == 0:
                    _let = morph.parse("месяцев ")[0]
                elif age == 1:
                    _let = morph.parse("месяц ")[0]
                elif age < 5:
                    _let = morph.parse("месяца ")[0]
                else:
                    _let = morph.parse("месяцев ")[0]
                r = "{0} {1}".format(age, _let.make_agree_with_number(age).word).strip()
                AgeCache(n=age, t=1, s=r).save()
        else:
            age = days
            ages = AgeCache.objects.filter(n=age, t=2)

            if ages.exists():
                r = ages[0].s
            else:
                import pymorphy2
                morph = pymorphy2.MorphAnalyzer()
                if age == 0:
                    _let = morph.parse("дней ")[0]
                elif age == 1:
                    _let = morph.parse("день ")[0]
                elif age < 5:
                    _let = morph.parse("дня ")[0]
                elif age <= 20:
                    _let = morph.parse("дней ")[0]
                elif 5 > age % 10 > 0:
                    _let = morph.parse("день")[0]
                else:
                    _let = morph.parse("дней ")[0]
                r = "{0} {1}".format(age, _let.make_agree_with_number(age).word).strip()
                AgeCache(n=age, t=2, s=r).save()
        return r

    def fio(self, short=False, dots=False, full=False, direction=None, npf=False, bd=False):

        if not short:
            if full:
                r = "{0} {1} {2}, {5}, {3:%d.%m.%Y} ({4})".format(self.family, self.name, self.patronymic,
                                                                  self.birthday, self.age_s(direction=direction),
                                                                  self.sex)
            elif not npf:
                r = "{} {} {}".format(self.family, self.name, self.patronymic).strip()
            elif bd:
                r = "{0} {1} {2}, {3:%d.%m.%Y}".format(self.family, self.name, self.patronymic,
                                                       self.birthday)
            else:
                r = "{} {} {}".format(self.name, self.patronymic, self.family).strip()
        else:
            def first_letter_not_blank(s):
                if len(s) > 0:
                    return " " + s[0] + ("." if dots else "")
                return ""

            r = "{0}{1}".format(self.family,
                                first_letter_not_blank(self.name) + first_letter_not_blank(self.patronymic).replace(" ",
                                                                                                                    "" if not dots else " "))
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

    def sync_with_tfoms(self):
        is_new = False
        updated = []

        enp_doc: [Document, None] = Document.objects.filter(document_type__title__startswith="Полис ОМС", individual=self).first()

        tfoms_data = None
        if enp_doc and enp_doc.number:
            from tfoms.integration import match_enp
            tfoms_data = match_enp(enp_doc.number)

        if not tfoms_data:
            from tfoms.integration import match_patient
            tfoms_data = match_patient(self.family, self.name, self.patronymic, strfdatetime(self.birthday, '%Y-%m-%d'))

        if tfoms_data:
            is_new = bool(self.tfoms_idp)
            updated = Individual.import_from_tfoms(tfoms_data, self)

        return is_new, updated

    @staticmethod
    def import_from_tfoms(data: dict, individual: ['Individual', None] = None, no_update=False):
        idp = data.get('idp')
        updated_data = []

        if idp:
            family = data.get('family', '').title()
            name = data.get('given', '').title()
            patronymic = data.get('patronymic', '').title()
            gender = data.get('gender', '').lower()
            birthday = datetime.strptime(data.get('birthdate', '').split(' ')[0], "%Y-%m-%d").date()
            address = data.get('address', '').title().replace('Ул.', 'ул.').replace('Д.', 'д.').replace('Кв.', 'кв.')
            enp = data.get('enp', '')
            passport_number = data.get('passport_number', '')
            passport_seria = data.get('passport_seria', '')
            snils = data.get('snils', '')

            if not individual:
                indv = Individual.objects.filter(
                    Q(tfoms_idp=idp) | Q(document__document_type__title='СНИЛС', document__number=snils) | Q(document__document_type__title='Полис ОМС', document__number=enp)) \
                    if snils else \
                    Individual.objects.filter(Q(tfoms_idp=idp) | Q(document__document_type__title='Полис ОМС', document__number=enp))
            else:
                indv = Individual.objects.filter(pk=individual.pk)

            if not indv.exists():
                i = Individual(
                    family=family,
                    name=name,
                    patronymic=patronymic,
                    birthday=birthday,
                    sex=gender,
                    tfoms_idp=idp,
                )
                i.save()
            else:
                if no_update:
                    print('No update')
                    return
                print('Update patient data')
                i = indv[0]
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

                if i.tfoms_idp != idp:
                    i.tfoms_idp = idp
                    updated.append('tfoms_idp')

                if updated:
                    print('Updated:', updated)
                    i.save(update_fields=updated)

            print(i)

            print('Sync documents')

            enp_type = DocumentType.objects.filter(title__startswith="Полис ОМС").first()
            snils_type = DocumentType.objects.filter(title__startswith="СНИЛС").first()
            passport_type = DocumentType.objects.filter(title__startswith="Паспорт гражданина РФ").first()

            if snils_type and snils:
                print('Sync SNILS')
                i.add_or_update_doc(snils_type, '', snils)

            if passport_type and passport_seria and passport_number:
                print('Sync PASSPORT')
                i.add_or_update_doc(passport_type, passport_seria, passport_number)

            enp_doc = None
            if enp_type and enp:
                print('Sync ENP')
                enp_doc = i.add_or_update_doc(enp_type, '', enp)

            print('Sync L2 card')
            print(Card.add_l2_card(individual=i, polis=enp_doc, address=address, force=True, updated_data=updated_data))

            i.time_tfoms_last_sync = timezone.now()
            i.save(update_fields=['time_tfoms_last_sync'])

        return updated_data

    def add_or_update_doc(self, doc_type: 'DocumentType', serial: str, number: str):
        ds = Document.objects.filter(individual=self, document_type=doc_type)
        if ds.count() > 1:
            ds.delete()

        ds = Document.objects.filter(individual=self, document_type=doc_type)
        if ds.count() == 0:
            d = Document(individual=self, document_type=doc_type, serial=serial, number=number)
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

            if updated:
                d.save(update_fields=updated)
        return d

    class Meta:
        verbose_name = 'Физическое лицо'
        verbose_name_plural = 'Физические лица'


class DocumentType(models.Model):
    title = models.CharField(max_length=60, help_text="Название типа документа")
    check_priority = models.IntegerField(default=0,
                                         help_text="Приоритет проверки документа (чем больше число - тем больше (сильнее) приоритет)")
    rmis_type = models.CharField(max_length=10, default=None, blank=True, null=True)

    def __str__(self):
        return "{} | {} | ^{}".format(self.pk, self.title, self.check_priority)

    class Meta:
        verbose_name = 'Вид документа'
        verbose_name_plural = 'Виды документов'


class Document(models.Model):
    document_type = models.ForeignKey(DocumentType, help_text="Тип документа", db_index=True, on_delete=models.CASCADE)
    serial = models.CharField(max_length=30, blank=True, help_text="Серия")
    number = models.CharField(max_length=30, blank=True, help_text="Номер")
    individual = models.ForeignKey(Individual, help_text="Пациент", db_index=True, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True, blank=True)
    date_start = models.DateField(help_text="Дата начала действия докумена", blank=True, null=True)
    date_end = models.DateField(help_text="Дата окончания действия докумена", blank=True, null=True)
    who_give = models.TextField(default="", blank=True)
    from_rmis = models.BooleanField(default=True, blank=True)
    rmis_uid = models.CharField(max_length=11, default=None, blank=True, null=True)

    @property
    def date_start_local(self):
        return localtime(self.date_start)

    @property
    def date_end_local(self):
        return localtime(self.date_end)

    def __str__(self):
        return "{0} {1} {2}, Активен - {3}, {4}".format(self.document_type, self.serial, self.number,
                                                        self.is_active, self.individual)

    @staticmethod
    def get_all_doc(docs):
        """
        возвращает словарь словарей documents. Данные о документах: паспорт : номер: серия, полис: номер, снислс: номер
        """
        documents = {
            'passport': {'num': "", 'serial': "", 'date_start': "", 'issued': ""},
            'polis': {'serial': "", 'num': "", 'issued': ""},
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
                if d["series"] != self.serial or \
                        d['number'] != self.number or \
                        d['issuerText'] != self.who_give or \
                        d['issueDate'] != self.date_start or \
                        d['expireDate'] != self.date_end or \
                        d['active'] != self.is_active:
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
                        }
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
    document = models.ForeignKey('clients.Document', db_index=True, on_delete=models.CASCADE)


class CardBase(models.Model):
    title = models.CharField(max_length=50, help_text="Полное название базы")
    short_title = models.CharField(max_length=4, help_text="Краткий код базы", db_index=True)
    is_rmis = models.BooleanField(help_text="Это РМИС?", default=False)
    hide = models.BooleanField(help_text="Скрыть базу", default=False)
    history_number = models.BooleanField(help_text="Ввод номера истории", default=False)
    internal_type = models.BooleanField(help_text="Внутренний тип карт", default=False)
    assign_in_search = models.ForeignKey("clients.CardBase", related_name="assign_in_search_base",
                                         help_text="Показывать результаты в поиске вместе с этой базой", null=True,
                                         blank=True, default=None,
                                         on_delete=models.SET_NULL)
    order_weight = models.SmallIntegerField(default=0)
    forbidden_create_napr = models.BooleanField(help_text="Запрет создания направлений", default=False)

    def __str__(self):
        return "{0} - {1}".format(self.title, self.short_title)

    class Meta:
        verbose_name = 'База карт'
        verbose_name_plural = 'Базы карт'


class District(models.Model):
    title = models.CharField(max_length=128)
    sort_weight = models.IntegerField(default=0, null=True, blank=True, help_text='Вес сортировки')
    is_ginekolog = models.BooleanField(help_text="Гинекологический участок", default=False)
    code_poliklinika = models.CharField(max_length=8, default='', help_text="Краткий код участка", db_index=True,
                                        blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Участок'
        verbose_name_plural = 'Участки'


class Card(models.Model):
    AGENT_CHOICES = (
        ('mother', "Мать"),
        ('father', "Отец"),
        ('curator', "Опекун"),
        ('agent', "Представитель"),
        ('payer', "Плательщик"),
        ('', 'НЕ ВЫБРАНО'),
    )

    AGENT_NEED_DOC = ['curator', 'agent']
    AGENT_CANT_SELECT = ['payer']

    number = models.CharField(max_length=20, blank=True, help_text="Идетификатор карты", db_index=True)
    base = models.ForeignKey(CardBase, help_text="База карты", db_index=True, on_delete=models.PROTECT)
    individual = models.ForeignKey(Individual, help_text="Пациент", db_index=True, on_delete=models.CASCADE)
    is_archive = models.BooleanField(default=False, blank=True, db_index=True)
    polis = models.ForeignKey(Document, help_text="Документ для карты", blank=True, null=True, default=None,
                              on_delete=models.SET_NULL)
    main_diagnosis = models.CharField(max_length=36, blank=True, default='', help_text="Основной диагноз",
                                      db_index=True)
    main_address = models.CharField(max_length=128, blank=True, default='', help_text="Адрес регистрации")
    fact_address = models.CharField(max_length=128, blank=True, default='', help_text="Адрес факт. проживания")
    work_place = models.CharField(max_length=128, blank=True, default='', help_text="Место работы")
    work_place_db = models.ForeignKey('contracts.Company', blank=True, null=True, default=None,
                                      on_delete=models.SET_NULL, help_text="Место работы из базы")
    work_position = models.CharField(max_length=128, blank=True, default='', help_text="Должность")
    mother = models.ForeignKey('self', related_name='mother_p', help_text="Мать", blank=True, null=True, default=None,
                               on_delete=models.SET_NULL)
    father = models.ForeignKey('self', related_name='father_p', help_text="Отец", blank=True, null=True, default=None,
                               on_delete=models.SET_NULL)
    curator = models.ForeignKey('self', related_name='curator_p', help_text="Опекун", blank=True, null=True,
                                default=None, on_delete=models.SET_NULL)
    curator_doc_auth = models.CharField(max_length=255, blank=True, default='', help_text="Документ-основание опекуна")
    agent = models.ForeignKey('self', related_name='agent_p', help_text="Представитель (из учреждения, родственник)",
                              blank=True, null=True, default=None, on_delete=models.SET_NULL)
    agent_doc_auth = models.CharField(max_length=255, blank=True, default='',
                                      help_text="Документ-оснвоание представителя")
    payer = models.ForeignKey('self', related_name='payer_p', help_text="Плательщик", blank=True, null=True,
                              default=None, on_delete=models.SET_NULL)

    who_is_agent = models.CharField(max_length=7, choices=AGENT_CHOICES, blank=True, default='',
                                    help_text="Законный представитель пациента", db_index=True)
    district = models.ForeignKey(District, default=None, null=True, blank=True, help_text="Участок",
                                 on_delete=models.SET_NULL)

    ginekolog_district = models.ForeignKey(District, related_name='ginekolog_district', default=None, null=True,
                                           blank=True, help_text="Участок",
                                           on_delete=models.SET_NULL)

    anamnesis_of_life = models.TextField(default='', blank=True, help_text='Анамнез жизни')
    number_poliklinika = models.CharField(max_length=20, blank=True, default='',
                                          help_text="Идетификатор карты поликлиника", db_index=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    harmful_factor = models.CharField(max_length=32, blank=True, default='')

    time_add = models.DateTimeField(default=timezone.now, null=True, blank=True)

    def __str__(self):
        return "{0} - {1}, {2}, Архив - {3}".format(self.number, self.base, self.individual, self.is_archive)

    def get_fio_w_card(self):
        return "L2 №{} {} {}".format(self.number, self.individual.fio(), self.individual.bd())

    def number_with_type(self):
        return "{}{}".format(self.number, (" " + self.base.short_title) if not self.base.is_rmis else "")

    def get_phones(self):
        return list(set([y for y in [x.normalize_number() for x in
                                     Phones.objects.filter(card__individual=self.individual, card__is_archive=False)]
                         + [Phones.nn(self.phone)]
                         if y and len(y) > 1]))

    def short_type_card(self):
        return "{}".format(self.base.short_title)

    def clear_phones(self, ts):
        to_delete = [x.pk for x in Phones.objects.filter(card=self) if x.number not in ts]
        Phones.objects.filter(pk__in=to_delete).delete()

    def add_phone(self, t: str):
        if not t:
            return
        t = t[:20]
        p, created = Phones.objects.get_or_create(card=self, number=t)
        p.normalize_number()

    def get_card_documents(self):
        types = [t.pk for t in DocumentType.objects.all()]
        docs = {}
        for t in types:
            CardDocUsage.objects.filter(card=self, document__document_type__pk=t, document__is_active=False).delete()
            if CardDocUsage.objects.filter(card=self, document__document_type__pk=t, document__is_active=True).exists():
                docs[t] = CardDocUsage.objects.filter(card=self, document__document_type__pk=t)[0].document_id
            elif Document.objects.filter(document_type__pk=t, individual=self.individual, is_active=True).exists():
                d = Document.objects.filter(document_type__pk=t, individual=self.individual, is_active=True).order_by(
                    '-id')[0]
                c = CardDocUsage(card=self, document=d)
                c.save()
                docs[t] = d.pk
            else:
                docs[t] = None
        return docs

    def get_data_individual(self, empty=False, full_empty=False):
        if not empty and full_empty:
            empty = full_empty
        """
        Получает на входе объект Карта
        возвращает словарь атрибутов по карте и Физ.лицу(Индивидуалу)
        :param card_object:
        :return:
        """
        ind_data = {'ind': self.individual} if not full_empty else {}
        ind_data['age'] = self.individual.age()
        docs = []
        cd = self.get_card_documents()
        for d in cd:
            if d and Document.objects.filter(pk=cd[d]).exists():
                docs.append(Document.objects.filter(pk=cd[d])[0])
        ind_data['doc'] = docs if not full_empty else []
        ind_data['fio'] = self.individual.fio()
        ind_data['born'] = self.individual.bd()
        ind_data[
            'main_address'] = "____________________________________________________" if not self.main_address and not full_empty \
            else self.main_address
        ind_data[
            'fact_address'] = "____________________________________________________" if not self.fact_address and not full_empty \
            else self.fact_address
        ind_data['card_num'] = self.number_with_type()
        ind_data['number_poliklinika'] = self.number_poliklinika
        ind_data['phone'] = self.get_phones()
        ind_data['work_place'] = self.work_place
        ind_data['work_place_db'] = self.work_place_db
        ind_data['work_position'] = self.work_position
        ind_data['sex'] = self.individual.sex

        # document "Паспорт РФ"
        ind_documents = Document.get_all_doc(docs)
        ind_data['passport_num'] = ind_documents['passport']['num']
        ind_data['passport_serial'] = ind_documents['passport']['serial']
        ind_data['passport_date_start'] = ind_documents['passport']['date_start']
        ind_data['passport_issued'] = "______________________________________________________________" \
            if not ind_documents['passport']['issued'] and not full_empty else ind_documents['passport']['issued']

        # document "св-во о рождении"
        ind_data['bc_num'] = ind_documents['bc']['num']
        ind_data['bc_serial'] = ind_documents['bc']['serial']
        ind_data['bc_date_start'] = ind_documents['bc']['date_start']
        ind_data['bc_issued'] = "______________________________________________________________" \
            if not ind_documents['bc']['issued'] and not full_empty else ind_documents['bc']['issued']
        if ind_data['passport_num']:
            ind_data['type_doc'] = 'паспорт'
        elif ind_data['bc_num']:
            ind_data['type_doc'] = 'свидетельство о рождении'
        else:
            ind_data['type_doc'] = ''

        # document= "снилс'
        ind_data['snils'] = ind_documents["snils"]["num"]
        # document= "полис ОМС"
        ind_data['oms'] = {}
        ind_data['oms']['polis_num'] = ind_documents["polis"]["num"]
        if not ind_data['oms']['polis_num']:
            ind_data['oms']['polis_num'] = None if empty else '___________________________'
        ind_data['oms']['polis_serial'] = ind_documents["polis"]["serial"]
        if not ind_data['oms']['polis_serial']:
            ind_data['oms']['polis_serial'] = None if empty else '________'
        # ind_data['oms']['polis_date_start'] = ind_documents["polis"]["date_start"]
        ind_data['oms']['polis_issued'] = (None if empty else '') if not ind_documents["polis"]["issued"] else \
            ind_documents["polis"]["issued"]

        return ind_data

    @staticmethod
    def next_l2_n():
        last_l2 = Card.objects.filter(base__internal_type=True).extra(
            select={'numberInt': 'CAST(number AS INTEGER)'}
        ).order_by("-numberInt").first()
        n = 0
        if last_l2:
            n = last_l2.numberInt
        return n + 1

    @staticmethod
    def add_l2_card(individual: [Individual, None] = None, card_orig: ['Card', None] = None, distinct=True, polis: ['Document', None] = None, address: [str, None] = None, force=False,
                    updated_data=None):
        if distinct and card_orig \
                and Card.objects.filter(individual=card_orig.individual if not force else (individual or card_orig.individual), base__internal_type=True).exists():
            return None

        if force and Card.objects.filter(individual=card_orig.individual if not force else (individual or card_orig.individual), base__internal_type=True).exists():
            c = Card.objects.filter(individual=card_orig.individual if not force else (individual or card_orig.individual), base__internal_type=True)[0]
            updated = []

            if c.main_address != address:
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
                print('Updated:', updated)
                c.save(update_fields=updated)

            return c

        with transaction.atomic():
            cb = CardBase.objects.select_for_update().filter(internal_type=True).first()
            if (not card_orig and not individual) or not cb:
                return
            c = Card(number=Card.next_l2_n(), base=cb,
                     individual=individual if individual else card_orig.individual,
                     polis=polis or (None if not card_orig else card_orig.polis),
                     main_diagnosis='' if not card_orig else card_orig.main_diagnosis,
                     main_address=address or ('' if not card_orig else card_orig.main_address),
                     fact_address='' if not card_orig else card_orig.fact_address)
            c.save()
            print('Created card')
            return c

    class Meta:
        verbose_name = 'Карта'
        verbose_name_plural = 'Карты'


class AnamnesisHistory(models.Model):
    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    text = models.TextField(help_text='Анамнез жизни')
    who_save = models.ForeignKey('users.DoctorProfile', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def created_at_local(self):
        return localtime(self.created_at)


class DispensaryReg(models.Model):
    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    diagnos = models.CharField(max_length=511, help_text='Диагноз Д-учета', default='', blank=True, db_index=True)
    illnes = models.CharField(max_length=511, help_text='Заболевание по которому состоит на учете', default='',
                              blank=True)
    spec_reg = models.ForeignKey(Speciality, related_name='doc_spec_start', default=None, blank=True, null=True,
                                 help_text="Профиль специальности", db_index=True, on_delete=models.CASCADE)
    doc_start_reg = models.ForeignKey(DoctorProfile, related_name='doc_start_reg', default=None, blank=True, null=True,
                                      db_index=True, help_text='Лечащий врач кто поставил на учет',
                                      on_delete=models.CASCADE)
    date_start = models.DateField(help_text='Дата постановки на Д-учет', db_index=True, default=None, blank=True,
                                  null=True)
    doc_end_reg = models.ForeignKey(DoctorProfile, related_name='doc_end_reg', default=None, blank=True, null=True,
                                    db_index=True, help_text='Лечащий врач, кто снял с учета',
                                    on_delete=models.CASCADE)
    date_end = models.DateField(help_text='Дата сняти с Д-учета', db_index=True, default=None, blank=True, null=True)
    why_stop = models.CharField(max_length=511, help_text='Причина снятия с Д-учета', default='', blank=True)

    class Meta:
        verbose_name = 'Д-учет'
        verbose_name_plural = 'Д-учет'


class Phones(models.Model):
    card = models.ForeignKey(Card, help_text="Карта", db_index=True, on_delete=models.CASCADE)
    number = models.CharField(max_length=20, help_text='Номер телефона')
    normalized_number = models.CharField(max_length=20, blank=True, default='', help_text='(NORMALIZED) Номер телефона')

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

    title = models.CharField(max_length=255, help_text='Каегория льготы')
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
    benefit = models.ForeignKey(BenefitType, related_name='benefit', help_text="Льгота", db_index=True,
                                on_delete=models.CASCADE)
    doc_start_reg = models.ForeignKey(DoctorProfile, related_name='doc_start_benefit', default=None, blank=True,
                                      null=True, db_index=True, help_text='Лечащий врач кто поставил на льготу',
                                      on_delete=models.CASCADE)
    date_start = models.DateField(help_text='Дата постановки на Льготу', db_index=True, default=None, blank=True,
                                  null=True)
    doc_end_reg = models.ForeignKey(DoctorProfile, related_name='doc_end_benefit', default=None, blank=True, null=True,
                                    db_index=True, help_text='Лечащий врач, кто снял с льготы',
                                    on_delete=models.CASCADE)
    date_end = models.DateField(help_text='Дата сняти с льготы', db_index=True, default=None, blank=True, null=True)
    registration_basis = models.TextField(default="", blank=True)


class VaccineReg(models.Model):
    STEPS = ('V', 'V1', 'V2', 'V3', 'V4', 'R', 'R1', 'R2', 'R3',)
    STEPS_CHOICES = ((x, x,) for x in STEPS)

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
