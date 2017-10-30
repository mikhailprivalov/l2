from django.db import models
import clients.models as Clients
from api.models import Application
from users.models import DoctorProfile
from jsonfield import JSONField
from researches.models import Tubes
import directory.models as directory
import simplejson as json
import users.models as umodels
import slog.models as slog


class FrequencyOfUseResearches(models.Model):
    research = models.ForeignKey(directory.Researches)
    user = models.ForeignKey(DoctorProfile)
    cnt = models.IntegerField(default=0)

    def __str__(self):
        return str(self.user) + " - " + str(self.research) + ", " + str(self.cnt)

    @staticmethod
    def inc(research, user):
        if not FrequencyOfUseResearches.objects.filter(research=research, user=user).exists():
            FrequencyOfUseResearches(research=research, user=user, cnt=0).save()

        f = FrequencyOfUseResearches.objects.get(research=research, user=user)
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
    research = models.ForeignKey(directory.Researches)
    user = models.ForeignKey(DoctorProfile)
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
    id = models.AutoField(primary_key=True)
    type = models.ForeignKey(directory.ReleationsFT, help_text='Тип пробирки')
    time_get = models.DateTimeField(null=True, blank=True, help_text='Время взятия материала', db_index=True)
    doc_get = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True,
                                related_name='docget', help_text='Кто взял материал')
    time_recive = models.DateTimeField(null=True, blank=True, help_text='Время получения материала', db_index=True)
    doc_recive = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True,
                                   related_name='docrecive', help_text='Кто получил материал')
    barcode = models.CharField(max_length=255, null=True, blank=True, help_text='Штрих-код или номер пробирки')

    notice = models.CharField(max_length=512, default="", blank=True, help_text='Замечания', db_index=True)

    daynum = models.IntegerField(default=0, blank=True, null=True,
                                 help_text='Номер принятия пробирки среди дня в лаборатории')

    def __str__(self):
        return "%d %s (%s, %s) %s" % (self.pk, self.type.tube.title, self.doc_get, self.doc_recive, self.notice)

    def day_num(self, doc, num):
        if not self.getstatus() and self.type.receive_in_lab:
            iss = Issledovaniya.objects.filter(tubes=self)
            if iss.count():
                self.set_get(iss[0].napravleniye.doc)
        new_t = False
        if not self.rstatus():
            new_t = True
            self.set_r(doc)
        if not self.daynum:
            '''from django.utils import timezone, datetime_safe
            last_num = 0
            date1 = datetime_safe.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            date2 = datetime_safe.datetime.now()
            if TubesRegistration.objects.filter(time_recive__range=(date1, date2), daynum__gt=0, issledovaniya__research__subgroup__podrazdeleniye=doc.podrazdeleniye).exists():
                last_num = max([x.daynum for x in TubesRegistration.objects.filter(time_recive__range=(date1, date2), daynum__gt=0, issledovaniya__research__subgroup__podrazdeleniye=doc.podrazdeleniye)])
            self.daynum = last_num + 1'''
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
        return (self.time_get is not None and self.doc_get is not None) or (self.type.receive_in_lab and one_by_one)

    def set_r(self, doc_r):
        """
        Установка статуса принятия материала лабораторией
        :param doc_r: врач/лаборант, принявший материал
        :return:
        """
        from django.utils import timezone
        self.time_recive = timezone.now()
        self.doc_recive = doc_r
        self.save()
        slog.Log(key=str(self.pk), user=doc_r, type=11,
                 body=json.dumps({"Замечание не приёма": self.notice})).save()

    def set_notice(self, doc_r, notice):
        """
        Установка замечания для пробирки
        :param doc_r: врач/лаборант, указавший замечание
        :param notice: текст замечания
        :return:
        """
        self.notice = notice
        self.save()
        slog.Log(key=str(self.pk), user=doc_r, type=12,
                 body=json.dumps({"Замечание не приёма": self.notice})).save()

    def clear_notice(self, doc_r):
        old_notice = self.notice
        self.notice = ""
        self.save()
        slog.Log(key=str(self.pk), user=doc_r, type=4000,
                 body=json.dumps({"Удалённое замечание": old_notice})).save()

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
        verbose_name = 'Пробирка для направления'
        verbose_name_plural = 'Пробирки для направлений'


class IstochnikiFinansirovaniya(models.Model):
    """
    Таблица источников финансирования
    """
    tilie = models.CharField(max_length=511, help_text='Название')
    active_status = models.BooleanField(default=True, help_text='Статус активности')
    base = models.ForeignKey(Clients.CardBase, help_text='База пациентов, к которой относится источник финансирования')
    hide = models.BooleanField(default=False, blank=True, help_text="Скрытие")

    class Meta:
        verbose_name = 'Источник финансирования'
        verbose_name_plural = 'Источники финансирования'


class Napravleniya(models.Model):
    """
    Таблица направлений
    """
    data_sozdaniya = models.DateTimeField(auto_now_add=True, help_text='Дата создания направления', db_index=True)
    diagnos = models.CharField(max_length=511, help_text='Время взятия материала')
    client = models.ForeignKey(Clients.Card, db_index=True, help_text='Пациент')
    doc = models.ForeignKey(DoctorProfile, db_index=True, help_text='Лечащий врач')
    istochnik_f = models.ForeignKey(IstochnikiFinansirovaniya, blank=True, null=True,
                                    help_text='Источник финансирования')
    is_printed = models.BooleanField(default=False, blank=True, help_text='Флаг - напечатано ли направление')
    time_print = models.DateTimeField(default=None, blank=True, null=True, help_text='Время печати')
    history_num = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='Номер истории')
    rmis_case_id = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='РМИС: Номер случая')
    rmis_hosp_id = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='РМИС: ЗОГ')
    rmis_resend_services = models.BooleanField(default=False, blank=True, help_text='Переотправить услуги?')
    doc_print = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_print",
                                  help_text='Профиль, который был использован при печати')
    doc_who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True,
                                       related_name="doc_who_create", help_text='Создатель направления')
    cancel = models.BooleanField(default=False, blank=True, help_text='Отмена направления')
    rmis_number = models.CharField(max_length=15, default=None, blank=True, null=True,
                                   help_text='ID направления в РМИС')
    result_rmis_send = models.BooleanField(default=False, blank=True, help_text='Результат отправлен в РМИС?')

    def __str__(self):
        return "%d для пациента %s (врач %s, выписал %s, %s, %s, %s)" % (
            self.pk, self.client.individual.fio(), self.doc.get_fio(), self.doc_who_create, self.rmis_number, self.rmis_case_id, self.rmis_hosp_id)

    @staticmethod
    def gen_napravleniye(client_id, doc, istochnik_f, diagnos, historynum, issledovaniya=None):
        """
        Генерация направления
        :param client_id: id пациента
        :param doc: л/врач
        :param istochnik_f: источник финансирования
        :param diagnos: диагноз
        :param patient_type: тип пациента (напр; поликлиника/стационар)
        :param issledovaniya: исследования (reserved)
        :return: созданое направление
        """
        if issledovaniya is None:
            issledovaniya = []
        dir = Napravleniya(client=Clients.Card.objects.get(pk=client_id),
                           doc=doc,
                           istochnik_f=istochnik_f,
                           diagnos=diagnos, cancel=False)

        if historynum != "":
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
    def gen_napravleniya_by_issledovaniya(client_id, diagnos, finsource, history_num, ofname_id, doc_current,
                                          researches, comments):
        res = {}  # Словарь с направлениями, сгруппированными по лабораториям
        researches_grouped_by_lab = []  # Лист с выбранными исследованиями по лабораториям
        i = 0
        result = {"r": False, "list_id": []}
        ofname = None
        if not doc_current.is_member(["Лечащий врач", "Оператор лечащего врача"]):
            result["message"] = "Недостаточно прав для создания направлений"
            return result
        if client_id and researches:  # если client_id получен и исследования получены
            if ofname_id > -1:
                ofname = umodels.DoctorProfile.objects.get(pk=ofname_id)

            no_attach = False
            conflict_list = []
            conflict_keys = []
            for v in researches:  # нормализация исследований
                researches_grouped_by_lab.append(
                    {v: researches[v]})

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
                                                                                                 history_num)
                            Napravleniya.set_of_name(directions_for_researches[dir_group], doc_current,
                                                     ofname_id, ofname)

                            result["list_id"].append(
                                directions_for_researches[dir_group].pk)  # Добавление ID в список созданых направлений
                        issledovaniye = Issledovaniya(napravleniye=directions_for_researches[dir_group],
                                                      # Установка направления для группы этого исследования
                                                      research=research,
                                                      deferred=False)  # Создание направления на исследование
                        issledovaniye.comment = comments.get(str(research.pk), "")[:10]
                        issledovaniye.save()  # Сохранение направления на исследование
                        FrequencyOfUseResearches.inc(research, doc_current)
                from rmis_integration.client import Client
                #c = Client()
                #for dk in directions_for_researches:
                #    c.directions.check_send(directions_for_researches[dk])
                result["r"] = True  # Флаг успешной вставки в True
                result["list_id"] = json.dumps(result["list_id"])  # Перевод списка созданых направлений в JSON строку
                slog.Log(key=json.dumps(result["list_id"]), user=doc_current, type=21,
                         body=json.dumps({"researches": [x for x in researches if x is not None],
                                          "client_num": Clients.Card.objects.get(pk=client_id).number,
                                          "client_id": client_id, "diagnos": diagnos,
                                          "finsource": finsource.tilie + " " + finsource.base.title,
                                          "history_num": history_num, "ofname": str(ofname),
                                          "comments": comments})).save()

            else:
                result["r"] = False
                result["message"] = "Следующие анализы не могут быть назначены вместе: " + ", ".join(conflict_list)
        return result

    def has_confirm(self):
        """
        Есть ли подтверждение у одного или более исследований в направлении
        :return: True, если есть подтверждение у одного или более
        """
        return any([x.doc_confirmation is not None for x in Issledovaniya.objects.filter(napravleniye=self)])

    def is_all_confirm(self):
        """
        Есть ли подтверждение у всех исследований в направлении
        :return: True, если всё подтверждено
        """
        return all([x.doc_confirmation is not None for x in Issledovaniya.objects.filter(napravleniye=self)])

    def is_has_deff(self):
        """
        Есть ли отложенные исследования
        :return: True, если подтверждены не все и есть одно или более отложенное исследование
        """
        return not self.is_all_confirm() and any([x.deferred for x in Issledovaniya.objects.filter(napravleniye=self)])

    class Meta:
        verbose_name = 'Направление'
        verbose_name_plural = 'Направления'


class Issledovaniya(models.Model):
    """
    Направления на исследования
    """
    napravleniye = models.ForeignKey(Napravleniya, help_text='Направление', db_index=True)
    research = models.ForeignKey(directory.Researches, null=True, blank=True,
                                 help_text='Вид исследования из справочника')
    tubes = models.ManyToManyField(TubesRegistration, help_text='Пробирки, необходимые для исследования', db_index=True)
    doc_save = models.ForeignKey(DoctorProfile, null=True, blank=True, related_name="doc_save", db_index=True,
                                 help_text='Профиль пользователя, сохранившего результат')
    time_save = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время сохранения результата')
    doc_confirmation = models.ForeignKey(DoctorProfile, null=True, blank=True, related_name="doc_confirmation",
                                         db_index=True, help_text='Профиль пользователя, подтвердившего результат')
    time_confirmation = models.DateTimeField(null=True, blank=True, db_index=True,
                                             help_text='Время подтверждения результата')
    deferred = models.BooleanField(default=False, blank=True, help_text='Флаг, отложено ли иследование')
    comment = models.CharField(max_length=10, default="", blank=True,
                               help_text='Комментарий (отображается на пробирке)')
    lab_comment = models.TextField(default="", null=True, blank=True, help_text='Комментарий, оставленный лабораторией')
    api_app = models.ForeignKey(Application, null=True, blank=True, default=None, help_text='Приложение API, через которое результаты были сохранены')

    def __str__(self):
        return "%d %s" % (self.napravleniye.pk, self.research.title)

    def is_get_material(self):
        """
        Осуществлен ли забор всего материала для исследования
        :return: True, если весь материал взят
        """
        return self.tubes.filter().exists() and all([x.doc_get is not None for x in self.tubes.filter()])

    def is_receive_material(self):
        """
        Осуществлен ли прием материала лабораторией
        :return: True, если весь материал принят
        """
        return self.is_get_material() and all([x.doc_recive is not None for x in self.tubes.filter()])

    def get_analyzer(self):
        return "" if not self.api_app else self.api_app.name

    class Meta:
        verbose_name = 'Назначение на исследование'
        verbose_name_plural = 'Назначения на исследования'


class RmisServices(models.Model):
    napravleniye = models.ForeignKey(Napravleniya, help_text='Направление', db_index=True)
    code = models.TextField(help_text='Код выгруженной услуги')
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
    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True,
                                      help_text='Направление на исследование, для которого сохранен результат')
    fraction = models.ForeignKey(directory.Fractions, help_text='Фракция из исследования', db_index=True)
    value = models.TextField(null=True, blank=True, help_text='Значение')
    iteration = models.IntegerField(default=1, null=True, help_text='Итерация')
    is_normal = models.CharField(max_length=255, default="", null=True, blank=True, help_text="Это норма?")
    ref_m = JSONField(default=None, blank=True, null=True, help_text="Референсы М")
    ref_f = JSONField(default=None, blank=True, null=True, help_text="Референсы Ж")
    ref_title = models.CharField(max_length=255, default=None, blank=True, null=True, help_text="Референсы Название")
    ref_about = models.TextField(default=None, blank=True, null=True, help_text="Референсы Описание")

    def __str__(self):
        return "%s | %s | %s" % (self.pk, self.fraction, self.ref_m is not None and self.ref_f is not None)

    def get_ref(self, as_str=False, full=False, fromsave=False, re_save=False):
        if (not self.ref_title and not fromsave) or re_save:
            self.ref_title = "Default" if self.fraction.default_ref is None else self.fraction.default_ref.title
            self.save()
            if not self.ref_m or re_save:
                self.ref_m = self.fraction.ref_m if self.fraction.default_ref is None else self.fraction.default_ref.ref_m
                self.save()

            if not self.ref_f or re_save:
                self.ref_f = self.fraction.ref_f if self.fraction.default_ref is None else self.fraction.default_ref.ref_f
                self.save()

            if not self.ref_about or re_save:
                self.ref_about = "" if self.fraction.default_ref is None else self.fraction.default_ref.about
                self.save()

        if full:
            return {"title": self.ref_title, "about": self.ref_about, "m": self.ref_m, "f": self.ref_f}

        ref = self.ref_f
        sex = self.issledovaniye.napravleniye.client.individual.sex.lower()
        if sex == "м":
            ref = self.ref_m

        if isinstance(ref, str):
            ref = json.loads(ref)
        if not ref:
            ref = {}

        if not as_str:
            return ref
        else:
            return json.dumps(ref)

    def get_is_norm(self, recalc=False):
        if self.is_normal == "" or recalc:
            norm = self.calc_normal()
            if self.is_normal != norm:
                self.save()
        else:
            norm = self.is_normal
        return norm

    def save(self, *args, **kw):
        self.is_normal = self.calc_normal(True)
        super(Result, self).save(*args, **kw)

    def calc_normal(self, fromsave=False):
        import operator
        from functools import reduce
        trues = {True: ["полож.", "положительно", "да", "положительный", "обнаружено"],
                 False: ["отриц.", "отрицательно", "нет", "1/0", "отрицательный", "не обнаружено"]}
        signs = {">": [">", "&gt;", "более", "старше"], "<": ["<", "&lt;", "до", "младше", "менее"]}

        calc = "maybe"

        value = self.value
        sex = self.issledovaniye.napravleniye.client.individual.sex.lower()
        age = self.issledovaniye.napravleniye.client.individual.age(iss=self.issledovaniye)

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

            mode = 0
            if any([x in v for x in signs["<"]]):
                mode = 1
            elif any([x in v for x in signs[">"]]):
                mode = 2

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

            if "младше" in r.lower():
                r = r.replace("младше", "").strip()
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

        def clc(r, val):
            result = "normal"
            if val.strip() != "":
                if val.lower().strip() == "гемолиз":
                    result = "not_normal"
                else:
                    for k in r.keys():
                        tmp_result = "normal"
                        rigth = rigths(k.strip().lower())

                        if not rigth:
                            tmp_result = "maybe"
                        elif rigth[0] <= age <= rigth[1]:
                            rigth_v = rigths_v(r[k].strip().lower())
                            if rigth_v == "":
                                tmp_result = "maybe"
                            else:
                                test_v = test_value(rigth_v, val)
                                if not test_v:
                                    tmp_result = "not_normal"
                        if result not in ["maybe", "not_normal"] or tmp_result == "maybe":
                            result = tmp_result
            return result

        calc = clc(ref, value)
        return calc

    class Meta:
        verbose_name = 'Результат исследования'
        verbose_name_plural = 'Результаты исследований'
