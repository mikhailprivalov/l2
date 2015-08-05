from __future__ import unicode_literals

from django.db import models
from datetime import date, datetime

class Importedclients(models.Model):
    """Пациенты из DBF"""
    num = models.IntegerField(unique=True, primary_key=False, blank=True, null=True)  # Номер карты
    family = models.CharField(max_length=255, blank=True, null=True)  # Фамилия
    name = models.CharField(max_length=255, blank=True, null=True)  # Имя
    twoname = models.CharField(max_length=255, blank=True, null=True)  # Отчество
    birthday = models.CharField(max_length=255, blank=True, null=True)  # Дата рождения
    client_id = models.AutoField(unique=True, primary_key=True)  # Идентификатор клиента
    type = models.CharField(max_length=64, blank=True, null=True)  # Тип (Поликлиника или стационар)
    sex = models.CharField(max_length=16, blank=True, null=True)  # Пол
    initials = models.CharField(max_length=16, blank=True, null=True)  # Инициалы

    class Meta:
        managed = False
        db_table = 'ImportedClients'

    def fio(self) -> str:
        return self.family + " " + self.name + " " + self.twoname

    def bd(self):
        return datetime.strptime(self.birthday.split(" ")[0], "%d.%m.%Y").date()

    def age(self):
        """Подсчет возраста"""
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
