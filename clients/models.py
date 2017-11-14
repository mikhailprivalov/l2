from django.db import models
from datetime import date

import sys

from rmis_integration.client import Client

TESTING = 'test' in sys.argv[1:] or 'jenkins' in sys.argv[1:]


class Individual(models.Model):
    family = models.CharField(max_length=120, blank=True, help_text="Фамилия", db_index=True)
    name = models.CharField(max_length=120, blank=True, help_text="Имя", db_index=True)
    patronymic = models.CharField(max_length=120, blank=True, help_text="Отчество", db_index=True)
    birthday = models.DateField(help_text="Дата рождения", db_index=True)
    sex = models.CharField(max_length=2, default="м", help_text="Пол", db_index=True)

    def sync_with_rmis(self):
        c = Client()
        ok = False
        rmis_uid = ""
        if Card.objects.filter(individual=self, base__is_rmis=True).exists():
            rmis_uid = Card.objects.filter(individual=self, base__is_rmis=True)[0].number
            ok = True

        if not ok:
            docs = Document.objects.filter(individual=self).exclude(document_type__check_priority=0).order_by("-document_type__check_priority")
            for document in docs:
                s = c.patients.search_by_document(document)
                if len(s) > 0:
                    rmis_uid = s[0]
                    ok = True
                if ok:
                    break

        if ok:
            data = c.patients.get_data(rmis_uid)
            upd = self.family != data["family"] or self.name != data["name"] or self.patronymic != data["patronymic"] or (self.birthday != data["birthday"] and data["birthday"] is not None)

            if upd:
                self.family = data["family"]
                self.name = data["name"]
                self.patronymic = data["patronymic"]
                if data["birthday"] is not None:
                    self.birthday = data["birthday"].strftime("%d.%m.%Y")
                self.sex = data["sex"]
                self.save()

        if not ok:
            query = {"surname": self.family, "name": self.name, "patrName": self.patronymic, "birthDate": self.birthday.strftime("%Y-%m-%d")}
            rows = c.patients.client.searchIndividual(**query)
            if len(query) == 1:
                rmis_uid = rows[0]
                ok = True

        if ok and rmis_uid != "":

            def get_key(d: dict, val):
                r = [key for key, v in d.items() if v == val]
                if len(r) > 0:
                    return r[0]
                return None

            document_ids = c.patients.client.getIndividualDocuments(rmis_uid)
            for document_id in document_ids:
                document_object = c.patients.client.getDocument(document_id)
                k = get_key(c.patients.local_types, document_object["type"])
                if k and document_object["active"]:
                    data = dict(document_type=DocumentType.objects.get(pk=k),
                                serial=document_object["series"] or "",
                                number=document_object["number"] or "",
                                individual=self,
                                is_active=True)
                    Document.objects.filter(document_type=data['document_type'], individual=self).delete()
                    docs = Document.objects.filter(document_type=data['document_type'],
                                                   serial=data['serial'],
                                                   number=data['number'])
                    if not docs.exists():
                        doc = Document(**data)
                        doc.save()
                        continue
                    else:
                        pass  # TODO: Объединение физ.лиц
        return ok

    def bd(self):
        return "{:%d.%m.%Y}".format(self.birthday)

    def age(self, iss=None):
        """
        Функция подсчета возраста
        """
        if iss is None or not iss.tubes.filter(time_recive__isnull=False).exists():
            today = date.today()
        else:
            today = iss.tubes.filter(time_recive__isnull=False).order_by("-time_recive")[0].time_recive.date()
        born = self.birthday
        try:
            birthday = born.replace(year=today.year)
        except ValueError:
            birthday = born.replace(year=today.year, month=born.month + 1, day=1)
        if birthday > today:
            return today.year - born.year - 1
        else:
            return today.year - born.year

    def age_s(self, iss=None, direction=None) -> str:
        """
        Формирование строки возраста: 10 лет, 101 год
        :return:
        """
        import pymorphy2

        morph = pymorphy2.MorphAnalyzer()
        if direction is not None:
            from directions.models import Issledovaniya
            iss = None
            i = Issledovaniya.objects.filter(tubes__time_recive__isnull=False).order_by("-tubes__time_recive")
            if i.exists():
                iss = i[0]
        age = self.age(iss=iss)
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
        return "{0} {1}".format(age, _let.make_agree_with_number(age).word).strip()

    def fio(self, short=False, dots=False, full=False):
        r = ""

        if not short:
            if full:
                r = "{0} {1} {2}, {5}, {3:%d.%m.%Y} ({4})".format(self.family, self.name, self.patronymic,
                                                                  self.birthday, self.age_s(), self.sex)
            else:
                r = "{} {} {}".format(self.family, self.name, self.patronymic).strip()
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
        return client.patients.get_rmis_id_for_individual(individual=self, update_rmis=update)

    def get_rmis_uid(self):
        if not Card.objects.filter(base__is_rmis=True, is_archive=False, individual=self).exists():
            return self.check_rmis()
        return self.check_rmis(False)

    class Meta:
        verbose_name = 'Физическое лицо'
        verbose_name_plural = 'Физические лица'


class DocumentType(models.Model):
    title = models.CharField(max_length=60, help_text="Название типа документа")
    check_priority = models.IntegerField(default=0, help_text="Приоритет проверки документа (чем больше число - тем больше (сильнее) приоритет)")

    def __str__(self):
        return "{} | {} | ^{}".format(self.pk, self.title, self.check_priority)

    class Meta:
        verbose_name = 'Вид документа'
        verbose_name_plural = 'Виды документов'


class Document(models.Model):
    document_type = models.ForeignKey(DocumentType, help_text="Тип документа", db_index=True)
    serial = models.CharField(max_length=30, blank=True, help_text="Серия")
    number = models.CharField(max_length=30, blank=True, help_text="Номер")
    individual = models.ForeignKey(Individual, help_text="Пациент", db_index=True)
    is_active = models.BooleanField(default=True, blank=True)
    date_start = models.DateField(help_text="Дата начала действия докумена", blank=True, null=True)
    date_end = models.DateField(help_text="Дата окончания действия докумена", blank=True, null=True)

    def __str__(self):
        return "{0} {1} {2}, Активен - {3}, {4}".format(self.document_type, self.serial, self.number,
                                                        self.is_active, self.individual)

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'


class CardBase(models.Model):
    title = models.CharField(max_length=50, help_text="Полное название базы")
    short_title = models.CharField(max_length=4, help_text="Краткий код базы", db_index=True)
    is_rmis = models.BooleanField(help_text="Это РМИС?", default=False)
    hide = models.BooleanField(help_text="Скрыть базу", default=False)
    history_number = models.BooleanField(help_text="Ввод номера истории", default=False)
    assign_in_search = models.ForeignKey("clients.CardBase", related_name="assign_in_search_base", help_text="Показывать результаты в поиске вместе с этой базой", null=True, blank=True, default=None)

    def __str__(self):
        return "{0} - {1}".format(self.title, self.short_title)

    class Meta:
        verbose_name = 'База карт'
        verbose_name_plural = 'Базы карт'


class Card(models.Model):
    number = models.CharField(max_length=20, blank=True, help_text="Идетификатор карты", db_index=True)
    base = models.ForeignKey(CardBase, help_text="База карты", db_index=True)
    individual = models.ForeignKey(Individual, help_text="Пациент", db_index=True)
    is_archive = models.BooleanField(default=False, blank=True, db_index=True)

    def __str__(self):
        return "{0} - {1}, {2}, Архив - {3}".format(self.number, self.base, self.individual, self.is_archive)

    def number_with_type(self):
        return "{}{}".format(self.number, (" " + self.base.short_title) if not self.base.is_rmis else "")

    class Meta:
        verbose_name = 'Карта'
        verbose_name_plural = 'Карты'
