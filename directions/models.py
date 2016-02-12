from django.db import models
from clients.models import Importedclients
from users.models import DoctorProfile
from jsonfield import JSONField
from researches.models import Researches, Tubes
import directory.models as directory
import simplejson as json
import users.models as umodels
import slog.models as slog

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
    def gen_napravleniye(client_id, doc, istochnik_f, diagnos, patient_type, historynum, issledovaniya=[]):
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
    def set_of_name(dir, doc_current, ofname_id, ofname):
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
    def gen_napravleniya_by_issledovaniya(client_id, diagnos, finsource, history_num, i, ofname_id, ptype, doc_current, res,
                                      researches, researches_grouped_by_lab):
        result = {"r": False, "list_id": []}
        checklist = []
        if not doc_current.is_member(["Лечащий врач", "Оператор лечащего врача"]):
            result["message"] = "Недостаточно прав для создания направлений"
            return result
        if client_id and researches:  # если client_id получен и исследования получены
            ofname = None
            if ofname_id > -1:
                ofname = umodels.DoctorProfile.objects.get(pk=ofname_id)

            no_attach = False
            conflict_list = []
            conflict_keys = []
            for v in researches:  # нормализация исследований
                if v and v not in checklist:
                    # checklist.append(v)
                    researches_grouped_by_lab.append(
                            {i: v})  # добавление словаря в лист, ключом которого является идентификатор исследования
                    # [{5:[0,2,5,7]},{6:[8]}] 5 - id лаборатории, [0,2,5,7] - id исследований из справочника

                    for vv in v:
                        if not vv or not vv.isnumeric():
                            continue
                        research_tmp = directory.Researches.objects.get(pk=int(vv))
                        if research_tmp.no_attach and research_tmp.no_attach > 0:
                            if research_tmp.no_attach not in conflict_keys:
                                conflict_keys.append(research_tmp.no_attach)
                                if not no_attach:
                                    conflict_list = [research_tmp.title]
                            else:
                                no_attach = True
                                conflict_list.append(research_tmp.title)
                i += 1

            for v in researches_grouped_by_lab:  # цикл перевода листа в словарь
                for key in v.keys():
                    res[key] = v[key]
                    # {5:[0,2,5,7],6:[8]}

            if not no_attach:
                directions_for_researches = {}  # Словарь для временной записи направлений.
                # Исследования привязываются к направлению по группе

                finsource = IstochnikiFinansirovaniya.objects.get(pk=finsource)  # получение источника финансирования

                for key in res:  # перебор лабораторий
                    for v in res[key]:  # перебор выбраных исследований в лаборатории
                        research = directory.Researches.objects.get(pk=v)  # получение объекта исследования по id

                        dir_group = -1
                        if research.direction:
                            dir_group = research.direction.pk  # получение группы исследования
                        # Если группа == 0, исследование не группируется с другими в одно направление
                        if dir_group >= 0 and dir_group not in directions_for_researches.keys():
                            # Если исследование может группироваться и направление для группы не создано

                            # Создание направления для группы
                            directions_for_researches[dir_group] = Napravleniya.gen_napravleniye(client_id,
                                                                                                 doc_current,
                                                                                                 finsource,
                                                                                                 diagnos,
                                                                                                 ptype,
                                                                                                 history_num)
                            Napravleniya.set_of_name(directions_for_researches[dir_group], doc_current,
                                                     ofname_id, ofname)

                            result["list_id"].append(
                                    directions_for_researches[dir_group].pk)  # Добавление ID в список созданых направлений
                        if dir_group < 0:  # если исследование не должно группироваться
                            dir_group = "id" + str(
                                    research.pk)  # формирование ключа (группы) для негруппируемого исследования

                            # Создание направления для исследования
                            directions_for_researches[dir_group] = Napravleniya.gen_napravleniye(client_id,
                                                                                                 doc_current,
                                                                                                 finsource,
                                                                                                 diagnos,
                                                                                                 ptype,
                                                                                                 history_num)
                            Napravleniya.set_of_name(directions_for_researches[dir_group], doc_current,
                                                     ofname_id, ofname)

                            result["list_id"].append(
                                    directions_for_researches[dir_group].pk)  # Добавление ID в список созданых направлений
                        issledovaniye = Issledovaniya(napravleniye=directions_for_researches[dir_group],
                                                      # Установка направления для группы этого исследования
                                                      research=research,
                                                      deferred=False)  # Создание направления на исследование
                        issledovaniye.save()  # Сохранение направления на исследование

                result["r"] = True  # Флаг успешной вставки в True
                result["list_id"] = json.dumps(result["list_id"])  # Перевод списка созданых направлений в JSON строку
                slog.Log(key=json.dumps(result["list_id"]), user=doc_current, type=21,
                         body=json.dumps(researches)).save()

            else:
                result["r"] = False
                result["message"] = "Следующие анализы не могут быть назначены вместе: " + ", ".join(conflict_list)
        return result



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
