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
        return f"{self.fio()} {self.bd()} ({self.age_s()}) {self.type_str(num=True)}"
