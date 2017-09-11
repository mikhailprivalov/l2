from __future__ import unicode_literals

from django.db import models
from datetime import date, datetime

import sys

TESTING = 'test' in sys.argv[1:] or 'jenkins' in sys.argv[1:]


class Importedclients(models.Model):
    """Пациенты из DBF"""
    num = models.IntegerField(unique=True, primary_key=False, blank=True, null=True, help_text='Номер карты')
    family = models.CharField(max_length=255, blank=True, null=True, help_text='Фамилия')
    name = models.CharField(max_length=255, blank=True, null=True, help_text='Имя')
    twoname = models.CharField(max_length=255, blank=True, null=True, help_text='Отчество')
    birthday = models.CharField(max_length=255, blank=True, null=True, help_text='Дата рождения')
    client_id = models.AutoField(unique=True, primary_key=True, help_text='Идентификатор клиента')
    type = models.CharField(max_length=64, blank=True, null=True, help_text='Тип (Поликлиника или стационар)')
    sex = models.CharField(max_length=16, blank=True, null=True, help_text='Пол')
    initials = models.CharField(max_length=16, blank=True, null=True, help_text='Инициалы')
    polis_serial = models.CharField(max_length=40, blank=True, null=True, help_text='Серия полиса ОМС')
    polis_number = models.CharField(max_length=40, blank=True, null=True, help_text='Номер полиса ОМС')

    class Meta:
        verbose_name = 'Пациент'
        verbose_name_plural = 'Пациенты'
        db_table = 'ImportedClients'

    def type_str(self, short=False, num=False):
        types = {"poli": "Поликлиника", "stat": "Стационар", "poli_stom": "Поликлиника-стоматология"}
        this_type = types.get(self.type, self.type)
        if short:
            this_type = "".join([x[0] for x in this_type.split("-")])
        if num:
            this_type = str(self.num) + " " + this_type
        return this_type

    def fio(self) -> str:
        """
        Функция возврата полного ФИО
        :return: Полное ФИО
        """
        return self.family + " " + self.name + " " + self.twoname

    def shortfio(self, supershort=False) -> str:
        """
        Функция возврата сокращенного ФИО
        :return: Короткое ФИО
        """
        r = ""
        if self.twoname and len(self.twoname) > 0:
            r = self.family + " " + self.name[0] + ". " + self.twoname[0] + "."
        else:
            r = self.family + " " + self.name[0] + "."
        if supershort:
            r = r.replace(". ", "").replace(".", "")
        return r

    def bd(self):
        """
        Возврат даты рождения
        :return: Дата рождения
        """
        return datetime.strptime(self.birthday.split(" ")[0], "%d.%m.%Y").date()

    def age(self):
        """
        Функция подсчета возраста
        """
        today = date.today()
        born = self.bd()
        try:
            birthday = born.replace(year=today.year)
        except ValueError:
            birthday = born.replace(year=today.year, month=born.month + 1, day=1)
        if birthday > today:
            return today.year - born.year - 1
        else:
            return today.year - born.year

    def age_s(self) -> str:
        """
        Формирование строки возраста: 10 лет, 101 год
        :return:
        """
        import pymorphy2

        morph = pymorphy2.MorphAnalyzer()
        age = self.age()
        if age < 5:
            _let = morph.parse("год")[0]
        elif age <= 20:
            _let = morph.parse("лет ")[0]
        elif 5 > age % 10 > 0:
            _let = morph.parse("год")[0]
        else:
            _let = morph.parse("лет ")[0]
        return "{0} {1}".format(age, _let.make_agree_with_number(age).word)

    def __str__(self):
        return self.fio() + " " + str(self.bd()) + " (" + self.age_s() + ") " + self.type_str(num=True)


class Individual(models.Model):
    family = models.CharField(max_length=120, blank=True, help_text="Фамилия", db_index=True)
    name = models.CharField(max_length=120, blank=True, help_text="Имя", db_index=True)
    patronymic = models.CharField(max_length=120, blank=True, help_text="Отчество", db_index=True)
    birthday = models.DateField(help_text="Дата рождения", db_index=True)
    sex = models.CharField(max_length=2, default="м", help_text="Пол")

    def bd(self):
        return "{:%d.%m.%Y}".format(self.birthday)

    def age(self):
        """
        Функция подсчета возраста
        """
        today = date.today()
        born = self.birthday
        try:
            birthday = born.replace(year=today.year)
        except ValueError:
            birthday = born.replace(year=today.year, month=born.month + 1, day=1)
        if birthday > today:
            return today.year - born.year - 1
        else:
            return today.year - born.year

    def age_s(self) -> str:
        """
        Формирование строки возраста: 10 лет, 101 год
        :return:
        """
        import pymorphy2

        morph = pymorphy2.MorphAnalyzer()
        age = self.age()
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

    def check_rmis(self, update=True):
        from rmis_integration.client import Client
        return Client().patients.get_rmis_id_for_individual(individual=self, update_rmis=update)

    def get_rmis_uid(self):
        if not Card.objects.filter(base__is_rmis=True, is_archive=False, individual=self).exists():
            return self.check_rmis()
        return self.check_rmis(False)


class DocumentType(models.Model):
    title = models.CharField(max_length=60, help_text="Название типа документа")

    def __str__(self):
        return "{0} | {1}".format(self.pk, self.title)


class Document(models.Model):
    document_type = models.ForeignKey(DocumentType, help_text="Тип документа")
    serial = models.CharField(max_length=30, blank=True, help_text="Серия")
    number = models.CharField(max_length=30, blank=True, help_text="Номер")
    individual = models.ForeignKey(Individual, help_text="Пациент")
    is_active = models.BooleanField(default=True, blank=True)
    date_start = models.DateField(help_text="Дата начала действия докумена", blank=True, null=True)
    date_end = models.DateField(help_text="Дата окончания действия докумена", blank=True, null=True)

    def __str__(self):
        return "{0} {1} {2}, Активен - {3}, {4}".format(self.document_type, self.serial, self.number,
                                                        self.is_active, self.individual)


class CardBase(models.Model):
    title = models.CharField(max_length=50, help_text="Полное название базы")
    short_title = models.CharField(max_length=4, help_text="Краткий код базы")
    is_rmis = models.BooleanField(help_text="Это РМИС?", default=False)
    hide = models.BooleanField(help_text="Скрыть базу", default=False)
    history_number = models.BooleanField(help_text="Ввод номера истории", default=False)

    def __str__(self):
        return "{0} - {1}".format(self.title, self.short_title)


class Card(models.Model):
    number = models.CharField(max_length=20, blank=True, help_text="Идетификатор карты")
    base = models.ForeignKey(CardBase, help_text="База карты")
    individual = models.ForeignKey(Individual, help_text="Пациент")
    is_archive = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return "{0} - {1}, {2}, Архив - {3}".format(self.number, self.base, self.individual, self.is_archive)

    def number_with_type(self):
        return "{}{}".format(self.number, (" " + self.base.short_title) if not self.base.is_rmis else "")
