import re
import unicodedata
import simplejson as json
from django.db import models
from django.utils import timezone
from jsonfield import JSONField

import clients.models as Clients
import directory.models as directory
import slog.models as slog
import users.models as umodels
import cases.models as cases
from api.models import Application
from laboratory.utils import strdate
from users.models import DoctorProfile


class FrequencyOfUseResearches(models.Model):
    research = models.ForeignKey(directory.Researches, on_delete=models.CASCADE)
    user = models.ForeignKey(DoctorProfile, db_index=True, on_delete=models.CASCADE)
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
    research = models.ForeignKey(directory.Researches, on_delete=models.CASCADE)
    user = models.ForeignKey(DoctorProfile, db_index=True, on_delete=models.CASCADE)
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
    id = models.AutoField(primary_key=True, db_index=True)
    type = models.ForeignKey(directory.ReleationsFT, help_text='Тип ёмкости', on_delete=models.CASCADE)
    time_get = models.DateTimeField(null=True, blank=True, help_text='Время взятия материала', db_index=True)
    doc_get = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True, related_name='docget', help_text='Кто взял материал', on_delete=models.SET_NULL)
    time_recive = models.DateTimeField(null=True, blank=True, help_text='Время получения материала', db_index=True)
    doc_recive = models.ForeignKey(DoctorProfile, null=True, blank=True, db_index=True, related_name='docrecive', help_text='Кто получил материал', on_delete=models.SET_NULL)
    barcode = models.CharField(max_length=255, null=True, blank=True, help_text='Штрих-код или номер ёмкости', db_index=True)

    notice = models.CharField(max_length=512, default="", blank=True, help_text='Замечания', db_index=True)

    daynum = models.IntegerField(default=0, blank=True, null=True,
                                 help_text='Номер принятия ёмкости среди дня в лаборатории')

    def __str__(self):
        return "%d %s (%s, %s) %s" % (self.pk, self.type.tube.title, self.doc_get, self.doc_recive, self.notice)

    def day_num(self, doc, num):
        if not self.getstatus():
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

        if not self.getstatus():
            self.set_get(doc_r)

        self.time_recive = timezone.now()
        self.doc_recive = doc_r
        self.save()
        slog.Log(key=str(self.pk), user=doc_r, type=11,
                 body=json.dumps({"Замечание не приёма": self.notice}) if self.notice != "" else "").save()

    def set_notice(self, doc_r, notice):
        """
        Установка замечания для пробирки
        :param doc_r: врач/лаборант, указавший замечание
        :param notice: текст замечания
        :return:
        """
        if notice != "":
            self.doc_recive = None
            self.time_recive = None
        self.notice = notice
        self.save()
        slog.Log(key=str(self.pk), user=doc_r, type=12,
                 body=json.dumps({"Замечание не приёма": self.notice})).save()

    def clear_notice(self, doc_r):
        old_notice = self.notice
        if old_notice == "":
            return
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
        verbose_name = 'Ёмкость для направления'
        verbose_name_plural = 'Ёмкости для направлений'

class PriceName(models.Model):
    title = models.CharField(max_length=511,unique=True, help_text='Наименование Прайса',db_index=True)
    active_status = models.BooleanField(default=True, help_text='Статус активности',db_index=True)
    date_start = models.DateField(help_text="Дата начала действия докумена", blank=True, null=True)
    date_end = models.DateField(help_text="Дата окончания действия докумена", blank=True, null=True)
    research = models.ManyToManyField(directory.Researches, through='PriceCoast', help_text="Услуга-Прайс", blank=True)

    def __str__(self):
        return "{}".format(self.title)


    def status(self):
        return self.active_status

    class Meta:
        verbose_name = 'Прайс - название'
        verbose_name_plural = 'Прайс - название'

class PriceCoast(models.Model):
    price_name = models.ForeignKey(PriceName, on_delete=models.DO_NOTHING,db_index=True)
    research = models.ForeignKey(directory.Researches, on_delete=models.DO_NOTHING,db_index=True)
    coast = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return "{}".format(self.price_name.title)

    class Meta:
        unique_together =('price_name','research','coast')
        verbose_name = 'Прайс - цены'
        verbose_name_plural = 'Прайс - цены'

class IstochnikiFinansirovaniya(models.Model):
    """
    Таблица источников финансирования
    """
    title = models.CharField(max_length=511, help_text='Название')
    price_name = models.ForeignKey(PriceName,null=True, default='',blank=True, help_text='Прайс',
                             db_index=True, on_delete=models.CASCADE)
    active_status = models.BooleanField(default=True, help_text='Статус активности')
    base = models.ForeignKey(Clients.CardBase, help_text='База пациентов, к которой относится источник финансирования', db_index=True, on_delete=models.CASCADE)
    hide = models.BooleanField(default=False, blank=True, help_text="Скрытие")
    rmis_auto_send = models.BooleanField(default=True, blank=True, help_text="Автоматическая отправка в РМИС")
    default_diagnos = models.CharField(max_length=36, help_text="Диагноз по умолчанию", default="", blank=True)

    def __str__(self):
        return "{} {} (скрыт: {})".format(self.base, self.title, self.hide)

    class Meta:
        verbose_name = 'Источник финансирования'
        verbose_name_plural = 'Источники финансирования'


class Diagnoses(models.Model):
    M = (
        (0, "Диапазон"),
        (1, "Группа"),
        (2, "Значение"),
    )
    code = models.CharField(max_length=255, db_index=True)
    title = models.TextField(db_index=True)
    parent = models.CharField(max_length=255, null=True, db_index=True)
    d_type = models.CharField(max_length=255, db_index=True)
    m_type = models.IntegerField(choices=M, db_index=True)

    def __str__(self):
        return "{} {}".format(self.code, self.title)


class RMISServiceInactive(models.Model):
    rmis_id = models.CharField(max_length=30, primary_key=True)
    enabled = models.BooleanField(default=True, blank=True)

    @staticmethod
    def checkInactive(serviceId, enabled):
        r = RMISServiceInactive.objects.filter(rmis_id=serviceId)
        if not r.exists() and enabled:
            RMISServiceInactive(rmis_id=serviceId, enabled=enabled).save()
        elif r.exists() and r[0].enabled != enabled:
            r[0].enabled = enabled
            r[0].save()

    @staticmethod
    def isInactive(serviceId):
        r = RMISServiceInactive.objects.filter(rmis_id=serviceId)
        return r.exists() and r[0].enabled

    def __str__(self):
        return "{} {}".format(self.rmis_id, self.enabled)


class RMISOrgs(models.Model):
    rmis_id = models.IntegerField(primary_key=True, editable=False)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class Napravleniya(models.Model):
    """
    Таблица направлений
    """
    data_sozdaniya = models.DateTimeField(auto_now_add=True, help_text='Дата создания направления', db_index=True)
    visit_date = models.DateTimeField(help_text='Дата посещения по направлению', db_index=True, default=None, blank=True, null=True)
    visit_who_mark = models.ForeignKey(DoctorProfile, related_name="visit_who_mark", default=None, blank=True, null=True, help_text='Профиль, который отметил посещение', on_delete=models.SET_NULL)
    diagnos = models.CharField(max_length=511, help_text='Диагноз', default='', blank=True)
    vich_code = models.CharField(max_length=12, help_text='Код для направления на СПИД', default='', blank=True)
    client = models.ForeignKey(Clients.Card, db_index=True, help_text='Пациент', on_delete=models.CASCADE)
    doc = models.ForeignKey(DoctorProfile, db_index=True, null=True, help_text='Лечащий врач', on_delete=models.CASCADE)
    istochnik_f = models.ForeignKey(IstochnikiFinansirovaniya, blank=True, null=True, help_text='Источник финансирования', on_delete=models.CASCADE)
    history_num = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='Номер истории')
    rmis_case_id = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='РМИС: Номер случая')
    rmis_hosp_id = models.CharField(max_length=255, default=None, blank=True, null=True, help_text='РМИС: ЗОГ')
    rmis_resend_services = models.BooleanField(default=False, blank=True, help_text='Переотправить услуги?', db_index=True)
    doc_who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_who_create", help_text='Создатель направления', on_delete=models.SET_NULL)
    cancel = models.BooleanField(default=False, blank=True, help_text='Отмена направления')
    rmis_number = models.CharField(max_length=15, default=None, blank=True, null=True, db_index=True, help_text='ID направления в РМИС')
    result_rmis_send = models.BooleanField(default=False, blank=True, help_text='Результат отправлен в РМИС?')
    imported_from_rmis = models.BooleanField(default=False, blank=True, db_index=True, help_text='Направление создано на основе направления из РМИС?')
    imported_org = models.ForeignKey(RMISOrgs, default=None, blank=True, null=True, on_delete=models.SET_NULL)
    imported_directions_rmis_send = models.BooleanField(default=False, blank=True, help_text='Для направления из РМИС отправлен бланк')
    force_rmis_send = models.BooleanField(default=False, blank=True, help_text='Подтверждение ручной отправки в РМИС')
    forcer_rmis_send = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_forcer_rmis_send", help_text='Исполнитель подтверждения отправки в РМИС', on_delete=models.SET_NULL)

    case = models.ForeignKey(cases.Case, default=None, blank=True, null=True, help_text='Случай обслуживания', on_delete=models.SET_NULL)

    def __str__(self):
        return "%d для пациента %s (врач %s, выписал %s, %s, %s, %s)" % (
            self.pk, self.client.individual.fio(), self.doc.get_fio(), self.doc_who_create, self.rmis_number, self.rmis_case_id, self.rmis_hosp_id)

    def get_instructions(self):
        r = []
        for i in Issledovaniya.objects.filter(napravleniye=self).exclude(research__instructions=""):
            r.append({"pk": i.research.pk, "title": i.research.title, "text": i.research.instructions})
        return r

    @staticmethod
    def gen_napravleniye(client_id, doc, istochnik_f, diagnos, historynum, doc_current, ofname_id, ofname, issledovaniya=None, save=True, for_rmis=None, rmis_data=None):
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
        if rmis_data is None:
            rmis_data = {}
        if issledovaniya is None:
            pass
        dir = Napravleniya(client=Clients.Card.objects.get(pk=client_id),
                           doc=doc if not for_rmis else None,
                           istochnik_f=istochnik_f,
                           data_sozdaniya=timezone.now(),
                           diagnos=diagnos, cancel=False)
        if for_rmis:
            dir.rmis_number = rmis_data.get("rmis_number")
            dir.imported_from_rmis = True
            dir.imported_org = RMISOrgs.objects.filter(rmis_id=rmis_data.get("imported_org", -1)).first()
            dir.doc = None
            dir.doc_who_create = doc_current
        else:
            if historynum != "":
                dir.history_num = historynum
            if ofname_id > -1 and ofname:
                dir.doc = ofname
                dir.doc_who_create = doc_current
        if save:
            dir.save()
        return dir

    @staticmethod
    def set_of_name(dir, doc_current, ofname_id, ofname: DoctorProfile):
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
                                          researches, comments, for_rmis=None, rmis_data=None, vich_code=''):
        if rmis_data is None:
            rmis_data = {}
        researches_grouped_by_lab = []  # Лист с выбранными исследованиями по лабораториям
        i = 0
        result = {"r": False, "list_id": []}
        ofname_id = ofname_id or -1
        ofname = None
        if not doc_current.is_member(["Лечащий врач", "Оператор лечащего врача"]):
            result["message"] = "Недостаточно прав для создания направлений"
            return result
        if not Clients.Card.objects.filter(pk=client_id).exists():
            result["message"] = "Карта в базе не зарегистрирована, попробуйте выполнить поиск заново"
            return result
        if client_id and researches:  # если client_id получен и исследования получены
            if ofname_id > -1:
                ofname = umodels.DoctorProfile.objects.get(pk=ofname_id)

            no_attach = False
            conflict_list = []
            conflict_keys = []
            for v in researches:  # нормализация исследований
                researches_grouped_by_lab.append({v: researches[v]})

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

            res = []
            for v in researches_grouped_by_lab:  # цикл перевода листа в словарь
                for key in v.keys():
                    res += v[key]
                    # {5:[0,2,5,7],6:[8]}

            if not no_attach:
                directions_for_researches = {}  # Словарь для временной записи направлений.
                # Исследования привязываются к направлению по группе

                finsource = IstochnikiFinansirovaniya.objects.filter(pk=finsource).first()

                for v in res:
                    research = directory.Researches.objects.get(pk=v)

                    dir_group = -1
                    if research.direction:
                        dir_group = research.direction.pk

                    if dir_group > -1 and dir_group not in directions_for_researches.keys():
                        directions_for_researches[dir_group] = Napravleniya.gen_napravleniye(client_id,
                                                                                             doc_current if not for_rmis else None,
                                                                                             finsource,
                                                                                             diagnos,
                                                                                             history_num,
                                                                                             doc_current,
                                                                                             ofname_id,
                                                                                             ofname,
                                                                                             for_rmis=for_rmis,
                                                                                             rmis_data=rmis_data)

                        result["list_id"].append(directions_for_researches[dir_group].pk)
                    if dir_group == -1:
                        dir_group = "id" + str(research.pk)
                        directions_for_researches[dir_group] = Napravleniya.gen_napravleniye(client_id,
                                                                                             doc_current if not for_rmis else None,
                                                                                             finsource,
                                                                                             diagnos,
                                                                                             history_num,
                                                                                             doc_current,
                                                                                             ofname_id,
                                                                                             ofname,
                                                                                             for_rmis=for_rmis,
                                                                                             rmis_data=rmis_data)

                        result["list_id"].append(directions_for_researches[dir_group].pk)
                    issledovaniye = Issledovaniya(napravleniye=directions_for_researches[dir_group],
                                                  research=research,
                                                  deferred=False)
                    issledovaniye.comment = (comments.get(str(research.pk), "") or "")[:10]
                    issledovaniye.save()
                    FrequencyOfUseResearches.inc(research, doc_current)
                for k, v in directions_for_researches.items():
                    if Issledovaniya.objects.filter(napravleniye=v, research__need_vich_code=True).exists():
                        v.vich_code = vich_code
                        v.save()
                result["r"] = True
                slog.Log(key=json.dumps(result["list_id"]), user=doc_current, type=21,
                         body=json.dumps({"researches": researches,
                                          "client_num": Clients.Card.objects.get(pk=client_id).number,
                                          "client_id": client_id, "diagnos": diagnos,
                                          "finsource": "" if not finsource else finsource.title + " " + finsource.base.title,
                                          "history_num": history_num, "ofname": str(ofname),
                                          "for_rmis": for_rmis,
                                          "rmis_data": rmis_data,
                                          "comments": comments})).save()

            else:
                result["r"] = False
                result["message"] = "Следующие исследования не могут быть назначены вместе: " + ", ".join(conflict_list)
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

    def department(self):
        if Issledovaniya.objects.filter(napravleniye=self).exists():
            return Issledovaniya.objects.filter(napravleniye=self)[0].research.podrazdeleniye
        return None

    def rmis_direction_type(self) -> str:
        dep = self.department()
        if dep:
            return dep.rmis_direction_type
        from rmis_integration.client import Settings
        return Settings.get("direction_type_title", default="Направление в лабораторию")

    def rmis_department_title(self) -> str:
        dep = self.department()
        if dep:
            return dep.rmis_department_title
        from rmis_integration.client import Settings
        return Settings.get("depname")

    def rmis_referral_title(self) -> str:
        return self.doc.podrazdeleniye.rmis_department_title

    class Meta:
        verbose_name = 'Направление'
        verbose_name_plural = 'Направления'


class Issledovaniya(models.Model):
    """
    Направления на исследования
    """
    napravleniye = models.ForeignKey(Napravleniya, help_text='Направление', db_index=True, on_delete=models.CASCADE)
    research = models.ForeignKey(directory.Researches, null=True, blank=True, help_text='Вид исследования из справочника', db_index=True, on_delete=models.CASCADE)
    tubes = models.ManyToManyField(TubesRegistration, help_text='Ёмкости, необходимые для исследования', db_index=True)
    doc_save = models.ForeignKey(DoctorProfile, null=True, blank=True, related_name="doc_save", db_index=True, help_text='Профиль пользователя, сохранившего результат', on_delete=models.SET_NULL)
    time_save = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время сохранения результата')
    doc_confirmation = models.ForeignKey(DoctorProfile, null=True, blank=True, related_name="doc_confirmation", db_index=True, help_text='Профиль пользователя, подтвердившего результат', on_delete=models.SET_NULL)
    time_confirmation = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время подтверждения результата')
    deferred = models.BooleanField(default=False, blank=True, help_text='Флаг, отложено ли иследование', db_index=True)
    comment = models.CharField(max_length=10, default="", blank=True, help_text='Комментарий (отображается на ёмкости)')
    lab_comment = models.TextField(default="", null=True, blank=True, help_text='Комментарий, оставленный лабораторией')
    api_app = models.ForeignKey(Application, null=True, blank=True, default=None, help_text='Приложение API, через которое результаты были сохранены', on_delete=models.SET_NULL)

    def __str__(self):
        return "%d %s" % (self.napravleniye.pk, self.research.title)

    def is_get_material(self):
        """
        Осуществлен ли забор всего материала для исследования
        :return: True, если весь материал взят
        """
        return self.tubes.filter().exists() and all([x.doc_get is not None for x in self.tubes.filter()])

    def get_visit_date(self):
        if not self.time_confirmation:
            return ""
        if not self.napravleniye.visit_date or not self.napravleniye.visit_who_mark:
            self.napravleniye.visit_date = timezone.now()
            self.napravleniye.visit_who_mark = self.doc_confirmation
            self.napravleniye.save()
        return strdate(self.napravleniye.visit_date)

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


class ParaclinicResult(models.Model):
    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True,
                                      help_text='Направление на исследование, для которого сохранен результат',
                                      on_delete=models.CASCADE)
    field = models.ForeignKey(directory.ParaclinicInputField, db_index=True,
                              help_text='Поле результата',
                              on_delete=models.CASCADE)

    value = models.TextField()


class RmisServices(models.Model):
    napravleniye = models.ForeignKey(Napravleniya, help_text='Направление', db_index=True, on_delete=models.CASCADE)
    code = models.TextField(help_text='Код выгруженной услуги', db_index=True)
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
    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True, help_text='Направление на исследование, для которого сохранен результат', on_delete=models.CASCADE)
    fraction = models.ForeignKey(directory.Fractions, help_text='Фракция из исследования', db_index=True, on_delete=models.CASCADE)
    value = models.TextField(null=True, blank=True, help_text='Значение')
    iteration = models.IntegerField(default=1, null=True, help_text='Итерация')
    is_normal = models.CharField(max_length=255, default="", null=True, blank=True, help_text="Это норма?")
    ref_m = JSONField(default=None, blank=True, null=True, help_text="Референсы М")
    ref_f = JSONField(default=None, blank=True, null=True, help_text="Референсы Ж")
    units = models.CharField(max_length=255, default=None, blank=True, null=True, help_text="Единицы измерения")
    ref_title = models.CharField(max_length=255, default=None, blank=True, null=True, help_text="Референсы Название")
    ref_about = models.TextField(default=None, blank=True, null=True, help_text="Референсы Описание")

    def __str__(self):
        return "%s | %s | %s" % (self.pk, self.fraction, self.ref_m is not None and self.ref_f is not None)

    def get_units(self, needsave=True):
        if not self.units and self.fraction.units and self.fraction.units != "":
            self.units = self.fraction.units
            if needsave:
                self.save()
        return self.units or ""

    def get_ref(self, as_str=False, full=False, fromsave=False, re_save=False, needsave=True):
        if (not self.ref_title and not fromsave) or re_save:
            self.ref_title = "Default" if self.fraction.default_ref is None else self.fraction.default_ref.title
            self.save()
            if not self.ref_m or re_save:
                self.ref_m = self.fraction.ref_m if self.fraction.default_ref is None else self.fraction.default_ref.ref_m
                if needsave:
                    self.save()

            if not self.ref_f or re_save:
                self.ref_f = self.fraction.ref_f if self.fraction.default_ref is None else self.fraction.default_ref.ref_f
                if needsave:
                    self.save()

            if not self.ref_about or re_save:
                self.ref_about = "" if self.fraction.default_ref is None else self.fraction.default_ref.about
                if needsave:
                    self.save()

        if full:
            return {"title": self.ref_title, "about": self.ref_about, "m": self.ref_m, "f": self.ref_f}

        ref = self.ref_f if self.issledovaniye.napravleniye.client.individual.sex.lower() != "м" else self.ref_m

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

    def calc_normal(self, fromsave=False, only_ref=False, raw_ref=True):
        import operator
        from functools import reduce
        trues = {True: ["полож.", "положительно", "да", "положительный", "обнаружено"],
                 False: ["отриц.", "отрицательно", "нет", "1/0", "отрицательный", "не обнаружено"]}
        signs = {">": [">", "&gt;", "более", "старше"], "<": ["<", "&lt;", "до", "младше", "менее"]}

        value = self.value
        days, monthes, years = self.issledovaniye.napravleniye.client.individual.age(iss=self.issledovaniye, days_monthes_years=True)

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
            '''
            if any([x in v for x in signs["<"]]):
                pass
            elif any([x in v for x in signs[">"]]):
                pass'''

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

            if "после" in r.lower():
                r = r.replace("после", "").strip()
                if r.isdigit():
                    return int(r), 200

            if "младше" in r.lower():
                r = r.replace("младше", "").strip()
                if r.isdigit():
                    return 0, int(r)

            if "до" in r.lower():
                r = r.replace("до", "").strip()
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

        def has_days(s: str):
            return any([x in s for x in ["дней", "день", "дн.", "дня"]])

        def has_monthes(s: str):
            return any([x in s for x in ["месяцев", "месяц", "мес.", "м.", "месяца"]])

        def not_days_and_m(s: str):
            return not has_days(s) and not has_monthes(s)

        def has_years(s: str):
            return any([x in s for x in ["лет", "год", "л.", "года"]] + [not has_days(s) and not has_monthes(s)])

        def clc(r, val, age, only_ref):
            result = "normal"
            active_ref = {}
            if val.strip() != "":
                for k in r.keys():
                    tmp_result = "normal"
                    kk = re.sub("[^0-9\-]", "", k)
                    rigth = rigths(k.strip().lower())
                    rigthkk = rigths(kk)

                    if years == 0 and rigthkk and not has_years(k):
                        print(days, monthes, years, k)
                        if monthes == 0:
                            if has_days(k):
                                rigth = rigthkk
                                age = days
                            else:
                                rigth = [-1, -1]
                        else:
                            if has_monthes(k):
                                rigth = rigthkk
                                age = monthes
                            else:
                                rigth = [-1, -1]
                    elif not not_days_and_m(k):
                        rigth = [-1, -1]

                    if not rigth:
                        tmp_result = "maybe"
                    elif rigth[0] <= age <= rigth[1]:
                        if not only_ref:
                            rigth_v = rigths_v(r[k].strip().lower())
                            pattern = re.compile(r"^([a-zA-Zа-яА-Я]|\s|:|,|\^|@|\\|\||/|\+|-|\(|\)|\[|\]|{|}|#|№|!|~|\.)+$")
                            if pattern.match(r[k]):
                                if self.compare(r[k], val):
                                    tmp_result = "normal"
                                else:
                                    tmp_result = "not_normal"
                            elif rigth_v == "":
                                tmp_result = "maybe"
                            else:
                                test_v = test_value(rigth_v, val)
                                if not test_v:
                                    tmp_result = "not_normal"
                        else:
                            if raw_ref:
                                active_ref = {"k": k, "r": r[k]}
                            else:
                                active_ref = rigths_v(r[k].strip().lower())
                    if result not in ["maybe", "not_normal"] or tmp_result == "maybe":
                        result = tmp_result
            if only_ref:
                return active_ref
            return result

        calc = clc(ref, value, years, only_ref)
        return calc

    class Meta:
        verbose_name = 'Результат исследования'
        verbose_name_plural = 'Результаты исследований'

    @staticmethod
    def NFD(text):
        return unicodedata.normalize('NFD', text)

    def canonical_caseless(self, text):
        return self.NFD(self.NFD(text).casefold())

    def compare(self, a: str, b: str):
        a = a.strip()
        b = b.strip()

        return self.canonical_caseless(a) == self.canonical_caseless(b)
