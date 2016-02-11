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
        if self.barcode and self.barcode.isnumeric():
            return self.barcode
        return self.id


class IstochnikiFinansirovaniya(models.Model):
    # Таблица источников финансирования
    tilie = models.CharField(max_length=511)  # Название
    active_status = models.BooleanField(default=True)  # Статус активности
    istype = models.CharField(max_length=4, default="poli")  # К поликлинике или стационару относится источник


class Napravleniya(models.Model):
    # Таблица направлений
    data_sozdaniya = models.DateTimeField(auto_now_add=True)  # Дата создания направления
    diagnos = models.CharField(max_length=511)  # Время взятия материала
    client = models.ForeignKey(Importedclients, db_index=True)  # Пациент
    doc = models.ForeignKey(DoctorProfile, db_index=True)  # Лечащий врач
    istochnik_f = models.ForeignKey(IstochnikiFinansirovaniya, blank=True, null=True)  # Источник финансирования
    is_printed = models.BooleanField(default=False, blank=True)
    time_print = models.DateTimeField(default=None, blank=True, null=True)
    history_num = models.CharField(max_length=255, default=None, blank=True, null=True)
    doc_print = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_print")
    doc_who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_who_create")  # Создатель направления
    cancel = models.BooleanField(default=False, blank=True)

    @staticmethod
    def genNapravleniye(client_id, doc, istochnik_f, diagnos, patient_type, historynum, issledovaniya=[]):
        """
        Генерация направления
        :param client_id: id пациента
        :param doc: л/врач
        :param istochnik_f: источник финансирования
        :param diagnos: диагноз
        :param patient_type: тип пациента (напр; поликлиника/стационар)
        :param historynum: номер истории в стационаре
        :param issledovaniya: исследования (reserved)
        :return: созданое направление
        """
        dir = Napravleniya(client=Importedclients.objects.get(pk=client_id),
                            doc=doc,
                            istochnik_f=istochnik_f,
                            diagnos=diagnos, cancel=False)

        if patient_type == "stat":
            dir.history_num = historynum
        dir.save()
        return dir
    @staticmethod
    def setOfName(dir, doc_current, ofname_id, ofname):
        """
        Проверка на выписывание направления от имени другого врача и установка этого имени в направление, если необходимо
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


class Issledovaniya(models.Model):
    # Направления на исследования
    napravleniye = models.ForeignKey(Napravleniya)  # Направление
    research = models.ForeignKey(directory.Researches, null=True, blank=True)  # Вид исследования из справочника
    # resultat = JSONField()  # Результат исследования в JSON
    tubes = models.ManyToManyField(TubesRegistration)
    doc_save = models.ForeignKey(DoctorProfile, null=True, blank=True, related_name="doc_save", db_index=True)
    time_save = models.DateTimeField(null=True, blank=True, db_index=True)
    doc_confirmation = models.ForeignKey(DoctorProfile, null=True, blank=True, related_name="doc_confirmation", db_index=True)
    time_confirmation = models.DateTimeField(null=True, blank=True, db_index=True)
    deferred = models.BooleanField(default=False, blank=True)



class Result(models.Model):
    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True)
    fraction = models.ForeignKey(directory.Fractions)
    value = models.CharField(max_length=255, null=True, blank=True)
    iteration = models.IntegerField(default=1, null=True)
