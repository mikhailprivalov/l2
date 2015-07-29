from django.db import models
from clients.models import Importedclients
from users.models import DoctorProfile
from jsonfield import JSONField
from researches.models import Researches, Tubes
import directory.models as directory

class TubesRegistration(models.Model):
    # Таблица с пробирками для исследований
    id = models.AutoField(primary_key=True)
    type = models.ForeignKey(directory.ReleationsFT)  # Тип пробирки
    time_get = models.DateTimeField(null=True, blank=True)  # Время взятия материала
    doc_get = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True,
                                related_name='docget')  # Кто взял материал
    time_recive = models.DateTimeField(null=True, blank=True)  # Время получения материала
    doc_recive = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True,
                                   related_name='docrecive')  # Кто получил материал
    barcode = models.CharField(max_length=255, null=True, blank=True)  # Штрих-код или номер пробирки

    notice = models.CharField(max_length=512, default="")  # Замечания

    def rstatus(self):
        if self.doc_recive:
            return True
        return False

    def getbc(self):
        if self.barcode.isnumeric():
            return self.barcode
        return self.id


class IstochnikiFinansirovaniya(models.Model):
    # Таблица источников финансирования
    tilie = models.CharField(max_length=511)  # Название
    active_status = models.BooleanField(default=True)  # Статус активности
    istype = models.CharField(max_length=4, default="poli")  # К поликлинике или стационару относится источник


class Napravleniya(models.Model):
    # Таблица направлений
    data_sozdaniya = models.DateTimeField(auto_now=True)  # Дата создания направления
    diagnos = models.CharField(max_length=511)  # Время взятия материала
    client = models.ForeignKey(Importedclients, db_index=True)  # Пациент
    doc = models.ForeignKey(DoctorProfile, db_index=True)  # Лечащий врач
    istochnik_f = models.ForeignKey(IstochnikiFinansirovaniya, blank=True, null=True)  # Источник финансирования


class Issledovaniya(models.Model):
    # Направления на исследования
    napravleniye = models.ForeignKey(Napravleniya)  # Направление
    research = models.ForeignKey(directory.Researches, null=True, blank=True)  # Вид исследования из справочника
    # resultat = JSONField()  # Результат исследования в JSON
    tubes = models.ManyToManyField(TubesRegistration)


class Result(models.Model):
    issledovaniye = models.ForeignKey(Issledovaniya)
    fraction = models.ForeignKey(directory.Fractions)
    value = models.CharField(max_length=255, null=True, blank=True)
    iteration = models.IntegerField(default=1, null=True)
