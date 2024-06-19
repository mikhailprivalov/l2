from django.contrib.auth.models import Group
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from jsonfield import JSONField

from laboratory.settings import DEATH_RESEARCH_PK
from podrazdeleniya.models import Podrazdeleniya
from researches.models import Tubes
from users.models import DoctorProfile, Speciality


class DirectionsGroup(models.Model):
    """
    Группы направлений
    """

    pass

    class Meta:
        verbose_name = "Группа направлений"
        verbose_name_plural = "Группы направлений"


class ReleationsFT(models.Model):
    """
    (многие-ко-многим) фракции к пробиркам
    """

    tube = models.ForeignKey(Tubes, help_text="Ёмкость", db_index=True, on_delete=models.CASCADE)
    receive_in_lab = models.BooleanField(default=False, blank=True, help_text="Приём пробирки в лаборатории разрешён без подтверждения забора")
    max_researches_per_tube = models.IntegerField(default=None, blank=True, null=True, help_text="Максимальное количество исследований для пробирки")
    is_default_external_tube = models.BooleanField(default=False, blank=True, db_index=True)

    @staticmethod
    def get_default_external_tube():
        tube = ReleationsFT.objects.filter(is_default_external_tube=True).first()

        if not tube:
            tube = ReleationsFT.objects.create(tube=Tubes.get_default_external_tube(), receive_in_lab=True, is_default_external_tube=True)

        return tube

    def __str__(self):
        return "%d %s" % (self.pk, self.tube.title)

    class Meta:
        verbose_name = "Физическая пробирка для фракций"
        verbose_name_plural = "Физические пробирки для фракций"


class ResearchGroup(models.Model):
    """
    Группы исследований
    """

    title = models.CharField(max_length=63, help_text="Название группы")
    lab = models.ForeignKey(Podrazdeleniya, null=True, blank=True, help_text="Лаборатория", db_index=True, on_delete=models.CASCADE)

    def __str__(self):
        return "%s" % self.title

    class Meta:
        verbose_name = "Группа исследований"
        verbose_name_plural = "Группы исследований"


class ResearchSite(models.Model):
    """
    Определяем абстрактные в РАЗДЕЛАХ - подразделы для размещения услуг
    в Консультации: первичные, повторные, медосмотры, др
    в Стоматология: терапевтическая, хирургическая, ортопедическая, др
    в Стационар: круглосуточный, дневной, др
    в Физиотерапевт: ЛФК, ФИЗИО, др.
    если в модели Research отсутствует ссылка на ResearchSite. То услуги выводить в корне
    """

    TYPES = (
        (0, "Консультация врача"),
        (1, "Лечение"),
        (2, "Стоматология"),
        (3, "Стационар"),
        (4, "Микробиология"),
        (7, "Формы"),
        (10, "Мониторинги"),
        (12, "Случаи"),
        (14, "Комплексные услуги"),
    )

    site_type = models.SmallIntegerField(choices=TYPES, help_text="Тип раздела", db_index=True)
    title = models.CharField(max_length=255, help_text="Подраздел")
    hide = models.BooleanField(default=False, blank=True, help_text="Скрытие подраздела", db_index=True)
    order = models.IntegerField(default=-999, help_text="Порядок")

    def __str__(self):
        return "%s" % self.title

    class Meta:
        verbose_name = "Подраздел"
        verbose_name_plural = "Подразделы"


class Localization(models.Model):
    title = models.CharField(max_length=64, help_text="Название места локализации")
    fsli = models.CharField(max_length=32, default=None, null=True, blank=True)
    barcode = models.CharField(max_length=15, default="", blank=True)

    def __str__(self):
        return "%s" % self.title

    class Meta:
        verbose_name = "Локализация"
        verbose_name_plural = "Локализации"


class ServiceLocation(models.Model):
    title = models.CharField(max_length=64, help_text="Название места оказания услуги")
    hide = models.BooleanField(help_text="Скрытие")

    def __str__(self):
        return "%s" % self.title

    class Meta:
        verbose_name = "Место оказания услуги"
        verbose_name_plural = "Места оказания услуг"


class MethodLaboratoryAnalisis(models.Model):
    title = models.CharField(max_length=64, help_text="Методика выполнения")

    def __str__(self):
        return "%s" % self.title

    class Meta:
        verbose_name = "Методика анализа"
        verbose_name_plural = "Методика анализа"


class LaboratoryMaterial(models.Model):
    title = models.CharField(max_length=64, help_text="Биоматериал")

    def __str__(self):
        return "%s" % self.title

    @staticmethod
    def get_materials():
        result = [{"id": material.pk, "label": material.title} for material in LaboratoryMaterial.objects.all()]
        return result

    class Meta:
        verbose_name = "Биоматериал"
        verbose_name_plural = "Биоматериалы"


class SubGroupDirectory(models.Model):
    title = models.CharField(max_length=64, help_text="Подгруппа услуги")

    def __str__(self):
        return "%s" % self.title

    class Meta:
        verbose_name = "Погруппа услуги"
        verbose_name_plural = "Подгруппы услуг"


class SubGroupPadrazdeleniye(models.Model):
    subgroup = models.ForeignKey(SubGroupDirectory, blank=True, default=None, null=True, help_text="Подгруппа", on_delete=models.CASCADE)
    podrazdeleniye = models.ForeignKey(Podrazdeleniya, help_text="Лаборатория", db_index=True, null=True, blank=True, default=None, on_delete=models.CASCADE)

    @staticmethod
    def get_subgroup_podrazdeleniye(podrazdeleniye):
        subgroups = SubGroupPadrazdeleniye.objects.filter(podrazdeleniye=podrazdeleniye)
        return [{"subgroupId": p.subgroup.pk, "id": p.subgroup.pk, "label": p.subgroup.title} for p in subgroups]

    @staticmethod
    def save_subgroups_department(department_pk, tb_data):
        podrazdeleniye = Podrazdeleniya.objects.filter(pk=department_pk).first()
        SubGroupPadrazdeleniye.objects.filter(podrazdeleniye=podrazdeleniye).delete()
        for t_b in tb_data:
            subgroup = SubGroupDirectory.objects.filter(pk=t_b["subgroupId"]).first()
            if subgroup:
                if not SubGroupPadrazdeleniye.objects.filter(podrazdeleniye=podrazdeleniye, subgroup=subgroup).exists():
                    SubGroupPadrazdeleniye(podrazdeleniye=podrazdeleniye, subgroup=subgroup).save()

        return True

    def __str__(self):
        return f"{self.subgroup.title} - {self.podrazdeleniye.title}"

    class Meta:
        verbose_name = "Свзяь погруппы и подздаления"
        verbose_name_plural = "Связи погрупп и подздалений"


class Researches(models.Model):
    """
    Вид исследования
    """

    DIRECTION_FORMS = (
        (0, "По умолчанию"),
        (38001, "38001. ИО - Направление на ВИЧ"),
        (38002, "38002. ИО - Направление на МСКТ"),
        (38003, "38003. ИО - Направление на COVID-19"),
        (38004, "38004. ИО - Направление на Микробиологию"),
        (38005, "38005. ИО - Направление в др. организацию"),
        (38006, "38006. ИО - Заявление на ВМП"),
        (38007, "38007. ИО - С параметрами по умолчанию"),
        (38008, "38008. ИО - Универсальное на бак.исследование"),
        (48001, "48001. ИО - Направление на Гистологию"),
        (38101, "38101. ИО - Направление в ИДЦ Ковид"),
        (38102, "38102. ИО - Направление в ИДЦ обследование"),
        (38103, "38103. ИО - Направление в СПИД-центр"),
        (38104, "38104. ИО - Направление на химико-токсикологические исследования"),
    )

    RESULT_FORMS = (
        (0, "По умолчанию"),
        (10001, "100.01 - Наркозная карта - анестезия"),
        (10002, "100.02 - Реанимационная карта - 1 день"),
        (10101, "101.01 - Дневник в 3 колонки"),
        (10201, "102.01 - Гистология"),
        (10202, "102.02 - Гистология2"),
        (10301, "103.01 - Справка-вождение"),
        (10401, "104.01 - Заключение на ВМП"),
        (10402, "104.02 - Направление на ВМП"),
        (10403, "104.03 - Рапорт на ВМП"),
        (10404, "104.04 - Заявление на возврат"),
        (10405, "104.05 - Анкета для оформления ЭЛН"),
        (10501, "105.01 - Свидетельство о смерти"),
        (10601, "106.01 - Свидетельство о о перинатальной смерти"),
        (10701, "107.01 - МСЭ"),
        (10801, "108.01 - 83-МПР"),
        (10901, "109.01 - 131/у"),
        (11001, "110.01 - Антирабическая карта"),
        (11002, "110.02 - Заключение ВК по психиатрическому освидетельствованию"),
        (11101, "111.01 - Карта профосмотра несовершеннолетнего N 030-ПО/у-17"),
        (11201, "112.01 - Извещение о НР ЛП"),
    )

    RESULT_TITLE_FORMS = (
        (0, "По умолчанию"),
        (10001, "100.01 - Выписка из амб карты"),
        (10002, "100.02 - Клеше"),
    )

    CO_EXECUTOR_MODES = (
        (0, "Нет"),
        (1, "1 со-исполнитель"),
        (2, "2 со-исполнителя"),
    )

    TYPE_SIZE_FORM = (
        (0, "По умолчанию"),
        (1, "Альбомный А4"),
    )

    PERIOD_HOUR = "PERIOD_HOUR"
    PERIOD_DAY = "PERIOD_DAY"
    PERIOD_WEEK = "PERIOD_WEEK"
    PERIOD_MONTH = "PERIOD_MONTH"
    PERIOD_QURTER = "PERIOD_QURTER"
    PERIOD_HALFYEAR = "PERIOD_HALFYEAR"
    PERIOD_YEAR = "PERIOD_YEAR"

    PERIOD_TYPES = (
        (PERIOD_HOUR, "Час"),
        (PERIOD_DAY, "День"),
        (PERIOD_WEEK, "Неделя"),
        (PERIOD_MONTH, "Месяц"),
        (PERIOD_QURTER, "Квартал"),
        (PERIOD_HALFYEAR, "Полгода"),
        (PERIOD_YEAR, "Год"),
    )

    direction = models.ForeignKey(DirectionsGroup, null=True, blank=True, help_text="Группа направления", on_delete=models.SET_NULL)
    title = models.CharField(max_length=255, default="", help_text="Название исследования", db_index=True)
    schedule_title = models.CharField(max_length=255, default="", help_text="Название для расписания", db_index=True)
    short_title = models.CharField(max_length=255, default="", blank=True)
    podrazdeleniye = models.ForeignKey(Podrazdeleniya, related_name="department", help_text="Лаборатория", db_index=True, null=True, blank=True, default=None, on_delete=models.CASCADE)
    quota_oms = models.IntegerField(default=-1, help_text="Квота по ОМС", blank=True)
    preparation = models.CharField(max_length=2047, default="", help_text="Подготовка к исследованию", blank=True)
    edit_mode = models.IntegerField(default=0, help_text="0 - Лаборант может сохранять и подтверждать. 1 - Лаборант сохраняет, врач должен подтвердить")
    hide = models.BooleanField(default=False, blank=True, help_text="Скрытие исследования", db_index=True)
    no_units_and_ref = models.BooleanField(default=False, blank=True, help_text="На бланке результата скрытие единиц измерения и референсов")
    no_attach = models.IntegerField(default=0, null=True, blank=True, help_text="Группа исследований, которые не могут быть назначены вместе")
    sort_weight = models.IntegerField(default=0, null=True, blank=True, help_text="Вес сортировки")
    template = models.IntegerField(default=0, blank=True, help_text="Шаблон формы")
    comment_variants = models.ForeignKey("directory.MaterialVariants", default=None, null=True, blank=True, help_text="Варианты комментариев к материалу", on_delete=models.SET_NULL)
    groups = models.ManyToManyField(ResearchGroup, blank=True, help_text="Группа исследований в лаборатории", db_index=True)
    onlywith = models.ForeignKey("self", null=True, blank=True, help_text="Без выбранного анализа не может быть назначено", on_delete=models.SET_NULL)
    can_lab_result_comment = models.BooleanField(default=False, blank=True, help_text="Возможность оставить комментарий лабораторией")
    code = models.TextField(default="", blank=True, help_text="Код исследования (несколько кодов разделяются точкой с запятой без пробелов)")
    is_paraclinic = models.BooleanField(default=False, blank=True, help_text="Это параклиническое исследование?", db_index=True)
    is_doc_refferal = models.BooleanField(default=False, blank=True, help_text="Это исследование-направление к врачу", db_index=True)
    is_treatment = models.BooleanField(default=False, blank=True, help_text="Это лечение", db_index=True)
    is_stom = models.BooleanField(default=False, blank=True, help_text="Это стоматология", db_index=True)
    is_hospital = models.BooleanField(default=False, blank=True, help_text="Это стационар", db_index=True)
    is_slave_hospital = models.BooleanField(default=False, blank=True, help_text="Это стационарный протокол", db_index=True)
    is_microbiology = models.BooleanField(default=False, blank=True, help_text="Это микробиологическое исследование", db_index=True)
    is_citology = models.BooleanField(default=False, blank=True, help_text="Это цитологическое исследование", db_index=True)
    is_gistology = models.BooleanField(default=False, blank=True, help_text="Это гистологическое исследование", db_index=True)
    is_form = models.BooleanField(default=False, blank=True, help_text="Это формы, cправки, направления", db_index=True)
    is_application = models.BooleanField(default=False, blank=True, help_text="Это заявление", db_index=True)
    is_direction_params = models.BooleanField(default=False, blank=True, help_text="Суррогатная услуга - параметры направления", db_index=True)
    is_global_direction_params = models.BooleanField(default=False, blank=True, help_text="Глобальные параметры", db_index=True)
    is_monitoring = models.BooleanField(default=False, blank=True, help_text="Это мониторинг", db_index=True)
    is_expertise = models.BooleanField(default=False, blank=True, help_text="Это экспертиза", db_index=True)
    is_aux = models.BooleanField(default=False, blank=True, help_text="Это вспомогательный", db_index=True)
    is_case = models.BooleanField(default=False, blank=True, help_text="Это случай", db_index=True)
    is_complex = models.BooleanField(default=False, blank=True, help_text="Это комплексная услуга", db_index=True)
    site_type = models.ForeignKey(ResearchSite, default=None, null=True, blank=True, help_text="Место услуги", on_delete=models.SET_NULL, db_index=True)
    need_vich_code = models.BooleanField(default=False, blank=True, help_text="Необходимость указания кода вич в направлении")
    paraclinic_info = models.TextField(blank=True, default="", help_text="Если это параклиническое исследование - здесь указывается подготовка и кабинет")
    instructions = models.TextField(blank=True, default="", help_text="Памятка для направления")
    not_grouping = models.BooleanField(default=False, blank=True, help_text="Нельзя группировать в направления?")
    direction_form = models.IntegerField(default=0, blank=True, choices=DIRECTION_FORMS, help_text="Форма направления")
    result_form = models.IntegerField(default=0, blank=True, choices=RESULT_FORMS, help_text="Форма результат")
    result_title_form = models.IntegerField(default=0, blank=True, choices=RESULT_TITLE_FORMS, help_text="Форма заголовка в бланке результат")
    size_form = models.IntegerField(default=0, blank=True, choices=TYPE_SIZE_FORM, help_text="Размеры формы результат")
    def_discount = models.SmallIntegerField(default=0, blank=True, help_text="Размер скидки")
    prior_discount = models.BooleanField(default=False, blank=True, help_text="Приоритет скидки")
    is_first_reception = models.BooleanField(default=False, blank=True, help_text="Эта услуга - первичный прием", db_index=True)
    internal_code = models.CharField(max_length=255, default="", help_text="Внутренний код исследования", blank=True, db_index=True)
    co_executor_mode = models.SmallIntegerField(default=0, choices=CO_EXECUTOR_MODES, blank=True)
    co_executor_2_title = models.CharField(max_length=40, default="Со-исполнитель", blank=True)
    microbiology_tube = models.ForeignKey(Tubes, blank=True, default=None, null=True, help_text="Пробирка для микробиологического исследования", on_delete=models.SET_NULL)
    localization = models.ManyToManyField(Localization, blank=True, default=None, help_text="Возможная локализация")
    service_location = models.ManyToManyField(ServiceLocation, blank=True, default=None, help_text="Возможные места оказаний")
    wide_headers = models.BooleanField(blank=True, default=False, help_text="Заголовки полей ввода на всю страницу")
    auto_add_hidden = models.ManyToManyField(
        "directory.Researches", related_name="res_auto_add_hidden", default=None, blank=True, help_text="Автоматически добавляемые назначения (не отображается в интерфейсе)"
    )
    vertical_result_display = models.BooleanField(blank=True, default=False, help_text="Отображение дат лабораторных тестов вертикально")

    bac_conclusion_templates = models.TextField(blank=True, default="", help_text="Шаблоны ввода для заключения")
    bac_culture_comments_templates = models.TextField(blank=True, default="", help_text="Шаблоны ввода для комментария в культуре")
    speciality = models.ForeignKey(Speciality, db_index=True, blank=True, default=None, null=True, help_text="Профиль-специальность услуги", on_delete=models.SET_NULL)
    rmis_id = models.CharField(max_length=128, db_index=True, blank=True, default=None, null=True)
    nsi_id = models.CharField(max_length=128, db_index=True, blank=True, default=None, null=True)
    has_own_form_result = models.BooleanField(blank=True, default=False, help_text="Собственная форма результатов")
    direction_params = models.ForeignKey("self", related_name="direction_params_p", help_text="Параметры направления", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    show_more_services = models.BooleanField(blank=True, default=True, help_text="Показывать Дополнительные услуги")
    type_period = models.CharField(max_length=20, null=True, blank=True, default=None, db_index=True, choices=PERIOD_TYPES, help_text="Тип периода")
    paddings_size = models.CharField(max_length=10, null=True, blank=True, default=None, help_text="Отступы для бланка результатов (лево| вверх|право|низ)")
    odii_type = models.PositiveSmallIntegerField(
        choices=Podrazdeleniya.ODII_TYPES, default=None, blank=True, null=True, help_text="Оказываемые виды инструментальных услуг (перезатирает из подразделения, если оно там указано)"
    )
    generator_name = models.CharField(max_length=60, null=True, blank=True, default=None, help_text="Название для xml-generator")
    expertise_params = models.ForeignKey("self", related_name="expertise_params_p", help_text="Экспертиза ", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    file_name_contract = models.CharField(max_length=60, null=True, blank=True, default="default", help_text="Название ф-ла контракта")
    method_lab_default = models.ForeignKey(MethodLaboratoryAnalisis, db_index=True, blank=True, default=None, null=True, help_text="Методика анализа по умолчанию", on_delete=models.SET_NULL)
    can_created_patient = models.BooleanField(blank=True, default=False, help_text="Может создаваться пациентом")
    enabled_add_files = models.BooleanField(blank=True, default=False, help_text="Можно добавить файлы")
    convert_to_doc_call = models.BooleanField(blank=True, default=False, help_text="Конвертировать форму в заявку DocCall")
    oid_kind = models.CharField(max_length=5, null=True, blank=True, default="", help_text="oid-документа 1.2.643.5.1.13.13.11.1520")
    oid_title = models.CharField(max_length=255, default="", db_index=True, help_text="oid-название документа 1.2.643.5.1.13.13.11.1520")
    uet_refferal_doc = models.FloatField(default=0, verbose_name="УЕТы врача", blank=True)
    uet_refferal_co_executor_1 = models.FloatField(default=0, verbose_name="УЕТы со-исполнителя 1", blank=True)
    print_additional_page_direction = models.CharField(max_length=255, default="", blank=True, verbose_name="Дополнительные формы при печати направления услуги")
    auto_register_on_rmis_location = models.CharField(max_length=128, db_index=True, blank=True, default="", null=True, help_text="Автозапись пациента на ближайший свободный слот")
    plan_external_performing_organization = models.ForeignKey("hospitals.Hospitals", blank=True, null=True, default=None, db_index=True, on_delete=models.SET_NULL)
    actual_period_result = models.SmallIntegerField(default=0, blank=True, help_text="Актуальность услуги в днях (для запрета)")
    cpp_template_files = models.TextField(max_length=500, default=None, null=True, blank=True, help_text="{1: 'название шаблона',2: 'название шаблона', 3: 'название шаблона'}")
    cda_template_file = models.CharField(max_length=50, db_index=True, blank=True, default="", null=True, help_text="название шаблона cda-шаблона")
    n3_id_med_document_type = models.SmallIntegerField(default=0, blank=True, help_text="N3 id_med_document_type")
    ecp_id = models.CharField(max_length=16, default="", blank=True, verbose_name="Код услуги в ЕЦП")
    laboratory_material = models.ForeignKey(LaboratoryMaterial, blank=True, default=None, null=True, help_text="Биоматериал", on_delete=models.SET_NULL)
    sub_group = models.ForeignKey(SubGroupDirectory, blank=True, default=None, null=True, help_text="Подгруппа", on_delete=models.SET_NULL)
    laboratory_duration = models.CharField(max_length=3, default="", blank=True, verbose_name="Срок выполнения")
    is_need_send_egisz = models.BooleanField(blank=True, default=False, help_text="Требуется отправка документав ЕГИСЗ")
    count_volume_material_for_tube = models.FloatField(default=0, verbose_name="Количество материала для емкости в долях", blank=True)

    @staticmethod
    def save_plan_performer(tb_data):
        research = Researches.objects.all()
        for r in research:
            r.plan_external_performing_organization = None
            r.save()

        for t_b in tb_data:
            research = Researches.objects.filter(pk=t_b["researchId"]).first()
            if research:
                research.plan_external_performing_organization_id = t_b["planExternalPerformerId"]
                research.save()
        return True

    @staticmethod
    def get_plan_performer():
        plan_performer = Researches.objects.filter(plan_external_performing_organization__isnull=False).order_by("title")
        return [{"researchId": p.id, "planExternalPerformerId": p.plan_external_performing_organization_id} for p in plan_performer]

    @staticmethod
    def filter_type(t):
        ts = {
            4: dict(is_paraclinic=True),
            5: dict(is_doc_refferal=True),
            6: dict(is_treatment=True),
            7: dict(is_stom=True),
            8: dict(is_hospital=True),
            9: dict(is_microbiology=True),
            10: dict(is_citology=True),
            11: dict(is_gistology=True),
            12: dict(is_form=True),
            13: dict(is_direction_params=True),
            14: dict(is_application=True),
            15: dict(is_monitoring=True),
            16: dict(is_expertise=True),
            17: dict(is_case=True),
            18: dict(is_complex=True),
        }
        return ts.get(t + 1, {})

    @property
    def is_doc_referral(self):
        return self.is_doc_refferal

    @property
    def reversed_type(self):
        if self.is_treatment:
            return -3
        if self.is_stom:
            return -4
        if self.is_hospital:
            return -5
        if self.is_form:
            return -9
        if self.is_direction_params:
            return -10
        if self.is_application:
            return -11
        if self.is_monitoring:
            return -12
        if self.is_expertise:
            return -13
        if self.is_microbiology or self.is_citology or self.is_gistology:
            return 2 - Podrazdeleniya.MORFOLOGY
        if self.is_case:
            return -14
        if self.is_complex:
            # -16 потому что на фронт отдаётся тип подразделения 18, на фронте 2 - 18 = -16
            # смотреть Researches.filter_type() complex=18 и SettingManager.en() complex=18
            # тип подразделения Podrazdeleniye.TYPES = 18,
            return -16
        return self.podrazdeleniye_id or -2

    @property
    def desc(self):
        return (
            self.is_treatment
            or self.is_stom
            or self.is_doc_refferal
            or self.is_paraclinic
            or self.is_microbiology
            or self.is_hospital
            or self.is_case
            or self.is_complex
            or self.is_citology
            or self.is_gistology
            or self.is_form
            or self.is_direction_params
            or self.is_monitoring
            or self.is_expertise
            or self.is_aux
        )

    def get_flag_types_n3(self):
        return {
            "title": self.title,
            "isHosp": self.is_hospital,
            "isDocReferral": self.is_doc_refferal,
            "isParaclinic": self.is_paraclinic,
            "isForm": self.is_form,
            "isDeathCertificate": self.pk == DEATH_RESEARCH_PK,
            "isDischarge": self.is_extract,
        }

    @property
    def can_transfer(self):
        if self.desc:
            return False
        return "перевод" in self.title.lower()

    @property
    def is_extract(self):
        if self.desc:
            return False
        return "выписка" in self.title.lower() or "выписной" in self.title.lower() or "посмертный" in self.title.lower()

    @property
    def r_type(self):
        if self.is_paraclinic:
            return "is_paraclinic"

        if self.is_doc_referral:
            return "consultation"

        if self.is_form:
            return "is_form"

        hs = HospitalService.objects.filter(slave_research=self).first()

        if hs:
            return HospitalService.TYPES_BY_KEYS_REVERSED.get(hs.site_type, "None")

        if self.podrazdeleniye and self.podrazdeleniye.p_type == Podrazdeleniya.LABORATORY:
            return "laboratory"

        return "None"

    def __str__(self):
        return "%s (Лаб. %s, Скрыт=%s)" % (self.title, self.podrazdeleniye, self.hide)

    def get_podrazdeleniye(self):
        return self.podrazdeleniye

    def get_podrazdeleniye_title(self):
        if self.is_microbiology:
            return self.microbiology_tube.title if self.microbiology_tube else ""
        return self.podrazdeleniye.title if self.podrazdeleniye else ""

    def get_podrazdeleniye_short_title(self):
        if self.is_microbiology:
            return self.microbiology_tube.title if self.microbiology_tube else ""
        return self.podrazdeleniye.get_title() if self.podrazdeleniye else ""

    def get_podrazdeleniye_title_recieve_recieve(self):
        if self.plan_external_performing_organization:
            result = self.plan_external_performing_organization.short_title
        elif self.is_microbiology:
            result = self.microbiology_tube.title if self.microbiology_tube else ""
        else:
            result = self.podrazdeleniye.title if self.podrazdeleniye else ""
        return result

    def get_title(self):
        return self.short_title or self.title

    def get_full_short_title(self):
        return self.title if self.get_title() == self.title else "{} ({})".format(self.title, self.get_title())

    def get_full_short_title_concat(self):
        if self.get_title() == self.title:
            return self.title
        return f"{self.title} – {self.short_title}"

    class Meta:
        verbose_name = "Вид исследования"
        verbose_name_plural = "Виды исследований"

    def get_site_type_id(self):
        if self.is_microbiology:
            return Podrazdeleniya.MORFOLOGY + 1
        if self.is_citology:
            return Podrazdeleniya.MORFOLOGY + 2
        if self.is_gistology:
            return Podrazdeleniya.MORFOLOGY + 3
        if self.is_application:
            return -13
        return self.site_type_id

    @staticmethod
    def as_json(research):
        result = {
            "pk": research.pk,
            "title": research.title,
            "internalCode": research.internal_code,
            "hide": research.hide,
            "order": research.sort_weight,
        }
        return result

    @staticmethod
    def get_tube_data(research_pk: int, need_fractions: bool = False) -> dict:
        fractions = Fractions.objects.filter(research_id=research_pk).select_related("relation__tube", "unit", "variants").order_by("relation_id", "sort_weight")
        research_tubes = {}
        for fraction in fractions:
            if research_tubes.get(fraction.relation_id) and need_fractions:
                fraction_data = fraction.as_json(fraction)
                fraction_data["refM"], fraction_data["refF"] = Fractions.convert_ref(fraction_data["refM"], fraction_data["refF"])
                research_tubes[fraction.relation_id]["fractions"].append(fraction_data)
            elif not research_tubes.get(fraction.relation_id):
                research_tubes[fraction.relation_id] = {
                    "id": fraction.relation_id,
                    "tubeId": fraction.relation.tube_id,
                    "color": fraction.relation.tube.color,
                    "title": f"{fraction.relation.tube.title} ({fraction.relation_id})",
                }
                if need_fractions:
                    fraction_data = fraction.as_json(fraction)
                    fraction_data["refM"], fraction_data["refF"] = Fractions.convert_ref(fraction_data["refM"], fraction_data["refF"])
                    research_tubes[fraction.relation_id]["fractions"] = [fraction_data]
        return research_tubes

    @staticmethod
    def get_laboratory_researches(podrazdelenie_id: int):
        if podrazdelenie_id == -1:
            podrazdeleniya = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY).values_list("pk", flat=True)
            researches = Researches.objects.filter(podrazdeleniye_id__in=podrazdeleniya).order_by("pk")
        else:
            researches = Researches.objects.filter(podrazdeleniye_id=podrazdelenie_id).order_by("pk")
        return researches

    @staticmethod
    def get_tubes(podrazdelenie_id: int):
        tubes = {}
        researches = Researches.get_laboratory_researches(podrazdelenie_id)
        for research in researches:
            research_tubes = Researches.get_tube_data(research.pk)
            tubes_info = [value for _, value in research_tubes.items()]
            tubes_keys = tuple(research_tubes.keys())
            if tubes.get(tubes_keys):
                tubes[tubes_keys]["researches"].append(research.as_json(research))
            else:
                tubes[tubes_keys] = {
                    "researches": [research.as_json(research)],
                    "tubes": tubes_info,
                }

        result = [{"researches": sorted(value["researches"], key=lambda d: d["order"]), "tubes": value["tubes"]} for _, value in tubes.items()]
        return result

    @staticmethod
    def update_order(research_pk: int, research_nearby_pk: int, action: str):
        research = Researches.objects.get(pk=research_pk)
        research_nearby = Researches.objects.get(pk=research_nearby_pk)
        if action == "inc_order":
            research.sort_weight += 1
            research_nearby.sort_weight -= 1
        elif action == "dec_order":
            research.sort_weight -= 1
            research_nearby.sort_weight += 1
        research.save()
        research_nearby.save()
        return True

    @staticmethod
    def change_visibility(research_pk: int):
        research = Researches.objects.get(pk=research_pk)
        if research.hide:
            research.hide = False
        else:
            research.hide = True
        research.save()
        return True

    @staticmethod
    def get_lab_research(research_pk: int):
        research = Researches.objects.get(pk=research_pk)
        research_tubes = Researches.get_tube_data(research_pk, True)
        result = {
            "pk": research.pk,
            "title": research.title,
            "shortTitle": research.short_title,
            "code": research.code,
            "internalCode": research.internal_code,
            "ecpId": research.ecp_id,
            "preparation": research.preparation,
            "departmentId": research.podrazdeleniye_id,
            "laboratoryMaterialId": research.laboratory_material_id,
            "subGroupId": research.sub_group_id,
            "laboratoryDuration": research.laboratory_duration,
            "volumeForTube": research.volume_for_tube,
            "tubes": [value for _, value in research_tubes.items()],
        }
        return result

    @staticmethod
    def update_lab_research(research_data):
        research_pk = None
        research_title = research_data["title"].strip() if research_data["title"] else None
        research_short_title = research_data["shortTitle"].strip() if research_data["shortTitle"] else ""
        research_ecp_id = research_data["ecpId"].strip() if research_data["ecpId"] else ""
        research_code = research_data["code"].strip() if research_data["code"] else ""
        research_internal_code = research_data["internalCode"].strip() if research_data["internalCode"] else ""
        research = Researches.objects.filter(pk=research_data["pk"]).first()
        fractions = None
        if research and research_title:
            research.title = research_title
            research.short_title = research_short_title
            research.code = research_code
            research.ecp_id = research_ecp_id
            research.internal_code = research_internal_code
            research.preparation = research_data["preparation"]
            research.podrazdeleniye_id = research_data["departmentId"]
            research.laboratory_material_id = research_data.get("laboratoryMaterialId", None)
            research.sub_group_id = research_data.get("subGroupId", None)
            research.laboratory_duration = research_data["laboratoryDuration"]
            research.volume_for_tube = research_data["volumeForTube"] if research_data["volumeForTube"] else 0
            research.save()
            fractions = Fractions.objects.filter(research_id=research.pk)
        elif research_title:
            research = Researches(
                title=research_title,
                short_title=research_short_title,
                ecp_id=research_ecp_id,
                code=research_code,
                internal_code=research_internal_code,
                preparation=research_data["preparation"],
                podrazdeleniye_id=research_data["departmentId"],
                laboratory_material_id=research_data.get("laboratoryMaterialId", None),
                sub_group_id=research_data.get("subGroupId", None),
                laboratory_duration=research_data["laboratoryDuration"],
                sort_weight=research_data["order"],
            )
            research.save()
            research_pk = research.pk
        else:
            return False
        for tube in research_data["tubes"]:
            relation = ReleationsFT.objects.filter(pk=tube["id"]).first()
            if not relation:
                tube_relation = Tubes.objects.filter(pk=tube["tubeId"]).first()
                relation = ReleationsFT(tube_id=tube_relation.pk)
                relation.save()
            for fraction in tube["fractions"]:
                current_fractions = None
                fraction_title = fraction["title"].strip() if fraction["title"] else ""
                ecp_id = fraction["ecpId"].strip() if fraction["ecpId"] else ""
                unit_id = fraction.get("unitId", None)
                ref_m, ref_f = Fractions.convert_ref(fraction["refM"], fraction["refF"], True)
                if fractions:
                    current_fractions = fractions.filter(pk=fraction["id"]).first()
                if current_fractions:
                    current_fractions.title = fraction_title
                    current_fractions.ecp_id = ecp_id
                    current_fractions.fsli = fraction.get("fsli", None)
                    current_fractions.sort_weight = fraction["order"]
                    current_fractions.unit_id = unit_id
                    current_fractions.variants_id = fraction.get("variantsId", None)
                    current_fractions.formula = fraction["formula"]
                    current_fractions.hide = fraction["hide"]
                    current_fractions.ref_m = ref_m
                    current_fractions.ref_f = ref_f
                    current_fractions.save()
                else:
                    new_fraction = Fractions(
                        research_id=research.pk,
                        title=fraction_title,
                        ecp_id=ecp_id,
                        fsli=fraction["fsli"],
                        unit_id=unit_id,
                        relation_id=relation.pk,
                        sort_weight=fraction["order"],
                        variants_id=fraction.get("variantsId", None),
                        formula=fraction["formula"],
                        hide=fraction["hide"],
                        ref_m=ref_m,
                        ref_f=ref_f,
                    )
                    new_fraction.save()
        if research_pk:
            return {"ok": True, "pk": research_pk}
        return {"ok": True}

    @staticmethod
    def get_lab_additional_data(research_pk: int):
        current_research = Researches.objects.get(pk=research_pk)
        result = {"instruction": current_research.instructions, "commentVariantsId": current_research.comment_variants_id, "templateForm": current_research.template}
        return result

    @staticmethod
    def get_complex_services(append_hide=True):
        if append_hide:
            complexs = Researches.objects.filter(is_complex=True).values_list("pk", "title").order_by("title")
        else:
            complexs = Researches.objects.filter(is_complex=True, hide=False).values_list("pk", "title").order_by("title")
        result = [{"id": complex[0], "label": complex[1]} for complex in complexs]
        return result

    @staticmethod
    def get_all_ids(array: bool = False, hide: bool = False):
        if array:
            result = list(Researches.objects.filter(hide=hide).values_list('id', flat=True))
        else:
            result = set(Researches.objects.filter(hide=hide).values_list('id', flat=True))
        return result


class HospitalService(models.Model):
    TYPES = (
        (0, "Первичный прием"),
        (1, "Дневник"),
        (2, "ВК"),
        (3, "Операция"),
        (4, "Назначения"),
        (5, "Физиотерапия"),
        (6, "Эпикриз"),
        (7, "Выписка"),
        (8, "Больничный лист"),
        (9, "t, ad, p – лист"),
        (11, "Формы"),
    )

    TYPES_BY_KEYS = {
        "primary receptions": 0,
        "diaries": 1,
        "vc": 2,
        "operation": 3,
        "assignments": 4,
        "physiotherapy": 5,
        "epicrisis": 6,
        "extracts": 7,
        "bl": 8,
        "t, ad, p sheet": 9,
    }

    TYPES_BY_KEYS_REVERSED = {
        0: "primary receptions",
        1: "diaries",
        2: "vc",
        3: "operation",
        4: "assignments",
        5: "physiotherapy",
        6: "epicrisis",
        7: "extracts",
        8: "bl",
        9: "t, ad, p sheet",
        11: "forms",
    }

    TYPES_REVERSED = {
        "paraclinical": "is_paraclinic",
        "laboratory": "is_lab",
        "consultation": "is_doc_refferal",
        "diaries": "diaries",
        "morfology": "is_morfology",
        "forms": "is_form",
        "all": "None",
    }

    main_research = models.ForeignKey(Researches, help_text="Стационарная услуга", on_delete=models.CASCADE, db_index=True)
    site_type = models.SmallIntegerField(choices=TYPES, help_text="Тип подраздела в стационарной карте", db_index=True)
    slave_research = models.ForeignKey(Researches, related_name="research_protocol", help_text="Протокол для вида услуги", on_delete=models.CASCADE)
    hide = models.BooleanField(default=False, blank=True, help_text="Скрытие услуги", db_index=True)

    def get_title(self):
        return f"{self.main_research.title} – {self.slave_research.get_full_short_title_concat()}"

    def __str__(self):
        return f"{self.main_research.title} - {self.site_type} - {self.slave_research.title} - {self.hide}"

    class Meta:
        verbose_name = "Стационарная услуга"
        verbose_name_plural = "Стационарные услуги"


class AuxService(models.Model):
    main_research = models.ForeignKey(Researches, help_text="Главная услуга", on_delete=models.CASCADE, db_index=True)
    aux_research = models.ForeignKey(Researches, related_name="aux_protocol", help_text="Вспомогательная услуга", on_delete=models.CASCADE)
    hide = models.BooleanField(default=False, blank=True, help_text="Скрытие услуги", db_index=True)

    class Meta:
        verbose_name = "Вспомогательная услуга"
        verbose_name_plural = "Вспомогательные услуги"

    def __str__(self):
        return f"{self.main_research.title} - {self.aux_research.title} - {self.hide}"


class ComplexService(models.Model):
    main_research = models.ForeignKey(Researches, help_text="Комплексная услуга", on_delete=models.CASCADE, db_index=True)
    slave_research = models.ForeignKey(Researches, related_name="slave_service", help_text="Простая услуга", on_delete=models.CASCADE)
    hide = models.BooleanField(default=False, blank=True, help_text="Скрытие услуги", db_index=True)

    class Meta:
        verbose_name = "Комплексная услуга"
        verbose_name_plural = "Комплексные услуги"

    def __str__(self):
        return f"{self.main_research.title} - {self.slave_research.title} - {self.hide}"

    @staticmethod
    def get_services_in_complex(complex_id: int):
        services = ComplexService.objects.filter(main_research_id=complex_id).select_related("slave_research").order_by("slave_research__title")
        result = [{"id": service.slave_research.pk, "label": service.slave_research.title, "hide": service.hide} for service in services]
        return result

    @staticmethod
    def check_complex(master_complex_id, slave_complex_services):
        master_complex_services = ComplexService.objects.filter(main_research_id=master_complex_id).values_list("slave_research_id", flat=True)
        master_complex_ids = set(master_complex_services)
        for service in slave_complex_services:
            if service.slave_research_id in master_complex_ids:
                return {"ok": False, "message": "В добавляемом комплексе пересекаются услуги"}
            if service.slave_research.is_complex:
                return {"ok": False, "message": "Нельзя добавить комплекс с комплексами"}
        return {"ok": True, "message": ""}

    @staticmethod
    def add_service(complex_id: int, service_id: int, ):
        if not complex_id or not service_id:
            return {"ok": False, "message": "Комплекс или услуга не переданы"}
        if complex_id == service_id:
            return {"ok": False, "message": "Нельзя добавить в комплекс этот же комплекс"}
        current_service: ComplexService = ComplexService.objects.filter(main_research_id=complex_id, slave_research_id=service_id).first()
        if current_service:
            return {"ok": False, "message": "Услуга уже есть"}
        slave_complex_service = ComplexService.objects.filter(main_research_id=service_id).select_related('slave_research')
        if slave_complex_service.exists():
            check_result = ComplexService.check_complex(complex_id, slave_complex_service)
            if not check_result["ok"]:
                return check_result
        complex_service = ComplexService(main_research_id=complex_id, slave_research_id=service_id)
        complex_service.save()
        return {"ok": True, "message": "", "result": complex_service.main_research_id}

    @staticmethod
    def change_hidden_complex(complex_id: int):
        complex = Researches.objects.get(pk=complex_id)
        if complex.hide:
            complex.hide = False
        else:
            complex.hide = True
        complex.save()
        return {"ok": True, "hide": complex.hide}

    @staticmethod
    def update_complex(complex_id: int, complex_title: str):
        complex_old_title = ''
        if complex_id:
            complex = Researches.objects.get(pk=complex_id)
            if complex.hide:
                return {"ok": False, "id": ""}
            complex_old_title = complex.title
            complex.title = complex_title
        else:
            complex = Researches(title=complex_title, is_complex=True)
        complex.save()
        return {"ok": True, "id": complex.pk, "old_title": complex_old_title}

    @staticmethod
    def change_service_hidden(complex_id: int, service_id: int):
        service_in_complex = ComplexService.objects.get(main_research_id=complex_id, slave_research_id=service_id)
        if service_in_complex.hide:
            service_in_complex.hide = False
        else:
            service_in_complex.hide = True
        service_in_complex.save()
        return {"ok": True, "hide": service_in_complex.hide}


class ParaclinicInputGroups(models.Model):
    title = models.CharField(max_length=255, help_text="Название группы")
    show_title = models.BooleanField()
    research = models.ForeignKey(Researches, on_delete=models.CASCADE)
    order = models.IntegerField()
    hide = models.BooleanField()
    visibility = models.TextField(default="", blank=True)
    fields_inline = models.BooleanField(default=False, blank=True)
    cda_option = models.ForeignKey("external_system.CdaFields", default=None, null=True, blank=True, help_text="CDA-поле для всей группы", on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.research.title} – {self.title}"

    class Meta:
        verbose_name = "Группы описательного протокола"
        verbose_name_plural = "Группы описательного протокола"


class PatientControlParam(models.Model):
    title = models.CharField(max_length=400, unique=True, help_text="Название название контролируемого параметра")
    code = models.CharField(max_length=400, help_text="Код параметра")
    all_patient_contol = models.BooleanField(default=False, blank=True, help_text="Контролировать у всех по умолчанию", db_index=True)
    order = models.IntegerField(default=-1)

    def __str__(self):
        return f"{self.title} - {self.code}"

    class Meta:
        verbose_name = "Контролируемый параметр справочник"
        verbose_name_plural = "Контролируемые параметры справочник"

    @staticmethod
    def get_patient_control_params():
        return [{"id": -1, "label": "Пусто"}, *[{"id": x.pk, "label": x.title} for x in PatientControlParam.objects.all().order_by("title")]]

    @staticmethod
    def get_all_patient_contol_param(code_param_id=None):
        if code_param_id:
            all_patient_contol = PatientControlParam.objects.filter(all_patient_contol=True, pk=code_param_id).order_by("order")
        else:
            all_patient_contol = PatientControlParam.objects.filter(all_patient_contol=True).order_by("order")
        return {cc.pk: {"title": cc.title, "purpose": ""} for cc in all_patient_contol}

    @staticmethod
    def get_contol_param_in_system():
        contol_param_system = PatientControlParam.objects.filter().order_by("order")
        return [{"id": cc.pk, "title": cc.title, "purpose": ""} for cc in contol_param_system]

    @staticmethod
    def as_json(param):
        json_data = {"pk": param.pk, "title": param.title, "code": param.code, "all_patient_control": param.all_patient_contol, "order": param.order}
        return json_data


class ParaclinicInputField(models.Model):
    TYPES = (
        (0, "Text"),
        (1, "Date"),
        (2, "MKB-10"),
        (3, "Calc"),
        (4, "purpose"),
        (5, "first_time"),
        (6, "result_reception"),
        (7, "outcome_illness"),
        (8, "maybe_onco"),
        (9, "List"),
        (10, "Dict"),
        (11, "Fraction"),
        (12, "Radio"),
        (13, "Protocol field"),
        (14, "Protocol raw field"),
        (15, "Rich text"),
        (16, "Agg lab"),
        (17, "Agg desc"),
        (18, "Number"),
        (19, "Number range"),
        (20, "Time HH:MM"),
        (21, "Anesthesia table"),
        (22, "Текст с автозаполнением"),
        (23, "Raw field without autoload"),
        (24, "Laboratory result test value units"),
        (25, "Diagnostic result"),
        (26, "Consultation result"),
        (27, "Table"),
        (28, "NSI directory"),
        (29, "FIAS address"),
        (30, "Генератор номера документа"),
        (31, "Прикрепление: МО-участок"),
        (32, "МКБ-внешние причины заболеваемости и смертности(1.2.643.5.1.13.13.99.2.692)"),
        (33, "МКБ-Алфавитный (1.2.643.5.1.13.13.11.1489)"),
        (34, "МКБ-обычный (1.2.643.5.1.13.13.11.1005)"),
        (35, "Врач"),
        (36, "МКБ-10(комбинация 1489, 692)"),
        (37, "Генератор номера перинатального МСС"),
        (38, "Procedure list result"),
        (39, "Динамический справочник"),
        (40, "Dynamic table"),
    )

    title = models.CharField(max_length=400, help_text="Название поля ввода")
    short_title = models.CharField(max_length=400, default="", blank=True, help_text="Синоним-короткое название поля ввода")
    group = models.ForeignKey(ParaclinicInputGroups, on_delete=models.CASCADE)
    patient_control_param = models.ForeignKey(PatientControlParam, default=None, null=True, blank=True, help_text="Контролируемый параметр", on_delete=models.SET_NULL)
    order = models.IntegerField()
    default_value = models.TextField(blank=True, default="")
    input_templates = models.TextField()
    hide = models.BooleanField()
    lines = models.IntegerField(default=3)
    field_type = models.SmallIntegerField(default=0, choices=TYPES, blank=True)
    required = models.BooleanField(default=False, blank=True)
    for_talon = models.BooleanField(default=False, blank=True)
    can_edit_computed = models.BooleanField(default=False, blank=True)
    sign_organization = models.BooleanField(default=False, blank=True, help_text="Подпись от организации")
    visibility = models.TextField(default="", blank=True)
    helper = models.CharField(max_length=999, blank=True, default="")
    for_extract_card = models.BooleanField(default=False, help_text="В выписку", blank=True)
    for_med_certificate = models.BooleanField(default=False, help_text="В справку", blank=True)
    attached = models.CharField(max_length=20, help_text="Скреплено с полем другой услуги", blank=True, default=None, null=True, db_index=True)
    not_edit = models.BooleanField(default=False, help_text="Не редактируемое", blank=True)
    control_param = models.TextField(default="", blank=True)
    operator_enter_param = models.BooleanField(default=False, help_text="Поле ввода для оператора(лаборанта)", blank=True)
    cda_option = models.ForeignKey("external_system.CdaFields", default=None, null=True, blank=True, help_text="CDA-поле для всей группы", on_delete=models.SET_NULL)
    denied_group = models.ForeignKey(Group, default=None, null=True, blank=True, on_delete=models.SET_NULL)

    def get_title(self, force_type=None, recursive=False):
        field_type = force_type or self.field_type
        titles = [""]
        if self.title:
            titles.append(self.title)
        if field_type != 14 and self.default_value.isdigit():
            if field_type == 11 and Fractions.objects.filter(pk=self.default_value).exists():
                f = Fractions.objects.get(pk=self.default_value)
                titles.append(f.research.title)
                if f.title not in titles:
                    titles[-1] = titles[-1] + " – " + f.title
            if field_type == 13 and ParaclinicInputField.objects.filter(pk=self.default_value).exists():
                f = ParaclinicInputField.objects.get(pk=self.default_value)
                titles.append(f.group.research.title)
                gt = f.group.title
                if gt not in titles:
                    titles[-1] = titles[-1] + " – " + gt
                ft = f.get_title(recursive=True)
                if ft not in titles and not recursive:
                    titles[-1] = titles[-1] + " – " + ft
        title = ", ".join([t for t in titles if t])
        return title

    def __str__(self):
        return f"{self.group.research.title} - {self.group.title} - {self.title}"

    class Meta:
        verbose_name = "Поля описательного протокола"
        verbose_name_plural = "Поля описательного протокола"


class ParaclinicTemplateName(models.Model):
    DEFAULT_TEMPLATE_TITLE = "По умолчанию"

    title = models.CharField(max_length=255, help_text="Название шаблона заполнения полей")
    research = models.ForeignKey(Researches, on_delete=models.CASCADE, db_index=True)
    hide = models.BooleanField(default=False, blank=True, help_text="Скрыть шаблон")

    def __str__(self):
        return "%s (Лаб. %s, Скрыт=%s)" % (self.title, self.research, self.hide)

    @staticmethod
    def make_default(research: Researches) -> "ParaclinicTemplateName":
        if not ParaclinicTemplateName.objects.filter(research=research, title=ParaclinicTemplateName.DEFAULT_TEMPLATE_TITLE).exists():
            with transaction.atomic():
                p = ParaclinicTemplateName(research=research, title=ParaclinicTemplateName.DEFAULT_TEMPLATE_TITLE)
                p.save()
                for f in ParaclinicInputField.objects.filter(group__research=research):
                    ParaclinicTemplateField(template_name=p, input_field=f, value=f.default_value).save()
        return ParaclinicTemplateName.objects.filter(research=research, title=ParaclinicTemplateName.DEFAULT_TEMPLATE_TITLE)[0]


class ParaclinicTemplateField(models.Model):
    template_name = models.ForeignKey(ParaclinicTemplateName, on_delete=models.CASCADE, db_index=True)
    input_field = models.ForeignKey(ParaclinicInputField, on_delete=models.CASCADE)
    value = models.TextField(help_text="Значение")

    def __str__(self):
        return "%s (%s, %s)" % (self.template_name, self.input_field.title, self.value)


class ParaclinicUserInputTemplateField(models.Model):
    doc = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, db_index=True)
    field = models.ForeignKey(ParaclinicInputField, on_delete=models.CASCADE, db_index=True)
    value = models.TextField(help_text="Значение")
    value_lower = models.TextField(help_text="Значение (для индексации)", db_index=True, null=True, blank=True)

    def __str__(self):
        return f"{self.field}, {self.value}"


class AutoAdd(models.Model):
    """
    Перечисление связей исследований, которые могут быть назначены только вместе (A только с B)
    """

    a = models.ForeignKey(Researches, help_text="Исследование, для которого устанавливается связь", db_index=True, related_name="a", on_delete=models.CASCADE)
    b = models.ForeignKey(Researches, help_text="Исследование, которое должно быть назначено вместе", related_name="b", on_delete=models.CASCADE)

    def __str__(self):
        return "%s -> %s" % (self.a.title, self.b.title)

    class Meta:
        verbose_name = "Автоматическое добавление назначений"
        verbose_name_plural = "Автоматическое добавления назначений"


class References(models.Model):
    """
    Справочник референсов
    """

    title = models.CharField(max_length=255, help_text="Название")
    about = models.TextField(help_text="Описание", blank=True)
    ref_m = JSONField(help_text="М")
    ref_f = JSONField(help_text="Ж")
    fraction = models.ForeignKey("Fractions", db_index=True, help_text="Фракция, к которой относится референс", on_delete=models.CASCADE)

    def __str__(self):
        return str(self.fraction) + " | " + str(self.fraction) + " | " + self.title

    class Meta:
        verbose_name = "Референс"
        verbose_name_plural = "Референсы"


class ResultVariants(models.Model):
    values = models.TextField(help_text='Варианты подсказок результатов, перечисленные через вертикальную черту без пробела "|"')

    def get_variants(self):
        return self.values.split("|")

    @staticmethod
    def get_all():
        result = [{"id": variants.pk, "label": variants.values} for variants in ResultVariants.objects.all()]
        return result

    def __str__(self):
        return str(self.get_variants())

    class Meta:
        verbose_name = "Вариант результата"
        verbose_name_plural = "Варианты результатов"


class MaterialVariants(models.Model):
    values = models.TextField(help_text='Варианты комментариев для материала, перечисленные через вертикальную черту без пробела "|"')

    def get_variants(self):
        return self.values.split("|")

    def __str__(self):
        return str(self.get_variants())

    @staticmethod
    def get_all():
        result = [{"id": variant.pk, "label": variant.values} for variant in MaterialVariants.objects.all()]
        return result

    class Meta:
        verbose_name = "Вариант комментария"
        verbose_name_plural = "Варианты комментариев"


# class Units(models.Model):
#     title = models.CharField(max_length=40, help_text="Единицы измерения")
#
#
#
# class SharedParameters(models.Model):
#     title = models.CharField(max_length=255, help_text='Название параметра')


class Unit(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название единицы измерения")
    short_title = models.CharField(max_length=255, db_index=True, verbose_name="Краткое название единицы измерения")
    code = models.CharField(max_length=4, db_index=True, verbose_name="Код")
    hide = models.BooleanField(default=False, blank=True, verbose_name="Скрытие")
    ucum = models.CharField(max_length=55, default="", blank=True, verbose_name="UCUM")

    @staticmethod
    def get_units():
        result = [
            {
                "id": unit.pk,
                "label": f"{unit.short_title} — {unit.title} - {unit.code}",
            }
            for unit in Unit.objects.filter(hide=False)
        ]
        return result

    def __str__(self) -> str:
        return f"{self.code} — {self.short_title} – {self.title}"


class Fractions(models.Model):
    """
    Фракции для исследований
    """

    title = models.CharField(max_length=255, verbose_name="Название фракции")
    research = models.ForeignKey(Researches, db_index=True, verbose_name="Исследование, к которому относится фракция", on_delete=models.CASCADE)
    units = models.CharField(max_length=255, verbose_name="Единицы измерения (DEPRECATED)", blank=True, default="")
    unit = models.ForeignKey(Unit, verbose_name="Единицы измерения", blank=True, default=None, null=True, on_delete=models.SET_NULL)
    default_ref = models.ForeignKey(References, verbose_name="Референс по-умолчанию", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    ref_m = JSONField(verbose_name="Референсы (М)", blank=True, default="{}")
    ref_f = JSONField(verbose_name="Референсы (Ж)", blank=True, default="{}")
    relation = models.ForeignKey(ReleationsFT, verbose_name="Пробирка (пробирки)", db_index=True, on_delete=models.CASCADE, null=True, default=None, blank=True)
    uet_doc = models.FloatField(default=0, verbose_name="УЕТы врача", blank=True)
    uet_co_executor_1 = models.FloatField(default=0, verbose_name="УЕТы со-исполнителя 1", blank=True)
    uet_co_executor_2 = models.FloatField(default=0, verbose_name="УЕТы со-исполнителя 2", blank=True)
    max_iterations = models.IntegerField(default=1, verbose_name="Максимальное число итераций", blank=True)
    variants = models.ForeignKey(ResultVariants, null=True, blank=True, verbose_name="Варианты подсказок результатов", on_delete=models.SET_NULL)
    variants2 = models.ForeignKey(ResultVariants, related_name="variants2", null=True, blank=True, verbose_name="Варианты подсказок результатов для Бак.лаб.", on_delete=models.SET_NULL)
    sort_weight = models.IntegerField(default=0, null=True, blank=True, verbose_name="Вес сортировки")
    hide = models.BooleanField(default=False, blank=True, verbose_name="Скрытие фракции", db_index=True)
    render_type = models.IntegerField(default=0, blank=True, verbose_name="Тип рендеринга (базовый тип (0) или динамическое число полей (1)")
    options = models.CharField(max_length=511, default="", blank=True, verbose_name="Варианты для динамического числа полей")
    formula = models.TextField(default="", blank=True, verbose_name="Формула для автоматического вычисления значения")
    code = models.CharField(max_length=16, default="", blank=True, verbose_name="Код фракции")
    print_title = models.BooleanField(default=False, blank=True, verbose_name="Печатать название(Группировка)", db_index=True)
    readonly_title = models.BooleanField(default=False, blank=True, verbose_name="Только для чтения-суррогатная группа для фракций", db_index=True)
    fsli = models.CharField(max_length=32, default=None, null=True, blank=True)
    patient_control_param = models.ForeignKey(PatientControlParam, default=None, null=True, blank=True, help_text="Контролируемый параметр", on_delete=models.SET_NULL)
    not_send_odli = models.BooleanField(help_text="Не отправлять данные в ОДЛИ", default=False)
    ecp_id = models.CharField(max_length=16, default="", blank=True, verbose_name="Код теста в ЕЦП")
    external_code = models.CharField(max_length=255, default="", help_text="Внешний код теста", blank=True, db_index=True)

    def get_unit(self):
        if self.unit:
            return self.unit
        if self.units:
            u = Unit.objects.filter(short_title=self.units).first()
            if u:
                self.unit = u
                self.save(update_fields=["unit"])
                return u
        return None

    def get_unit_str(self):
        u = self.get_unit()
        if u:
            return u.short_title
        return self.units

    def get_fsli_code(self):
        return (self.fsli or "").strip()

    def get_ecp_code(self):
        return (self.ecp_id or "").strip()

    @staticmethod
    def as_json(fraction) -> dict:
        result = {
            "id": fraction.pk,
            "title": fraction.title,
            "unitId": fraction.unit_id,
            "ecpId": fraction.ecp_id,
            "fsli": fraction.fsli,
            "order": fraction.sort_weight,
            "variantsId": fraction.variants_id,
            "formula": fraction.formula,
            "hide": fraction.hide,
            "refM": fraction.ref_m,
            "refF": fraction.ref_f,
        }
        return result

    @staticmethod
    def convert_ref(ref_m, ref_f, for_save=False):
        if for_save:
            convert_ref_m = {ref["age"].strip(): ref["value"].strip() for ref in ref_m if ref_m}
            convert_ref_f = {ref["age"].strip(): ref["value"].strip() for ref in ref_f if ref_f}
        else:
            convert_ref_m = [{"age": key, "value": value} for key, value in ref_m.items()] if isinstance(ref_m, dict) else []
            convert_ref_f = [{"age": key, "value": value} for key, value in ref_f.items()] if isinstance(ref_f, dict) else []
        return convert_ref_m, convert_ref_f

    def __str__(self):
        return self.research.title + " | " + self.title

    class Meta:
        verbose_name = "Фракция"
        verbose_name_plural = "Фракции"


class Absorption(models.Model):
    """
    Поглощение
    """

    fupper = models.ForeignKey(Fractions, related_name="fupper", help_text="Какая фракция главнее", db_index=True, on_delete=models.CASCADE)
    flower = models.ForeignKey(Fractions, related_name="flower", help_text="Какая фракция поглощается главной", on_delete=models.CASCADE)

    def __str__(self):
        return self.flower.__str__() + " -> " + self.fupper.__str__()

    class Meta:
        verbose_name = "Поглощение фракции"
        verbose_name_plural = "Поглощения фракций"


class NameRouteSheet(models.Model):
    """
    Route list for research. Маршрутный лист для исследований
    """

    title = models.CharField(max_length=255, unique=True, help_text="Название маршрутного листа")
    static_text = models.TextField(default="", help_text="Текст перед списком")

    def __str__(self):
        return "{}".format(self.title)

    def get_title(self):
        return self.title

    class Meta:
        verbose_name = "Cписки маршрутов"
        verbose_name_plural = "Списки маршрутов"


class DispensaryRouteSheet(models.Model):
    SEX = (
        ("м", "м"),
        ("ж", "ж"),
    )

    age_client = models.PositiveSmallIntegerField(db_index=True, help_text="Возраст", null=False, blank=False)
    sex_client = models.CharField(max_length=1, choices=SEX, help_text="Пол", db_index=True)
    research = models.ForeignKey(Researches, db_index=True, help_text="Исследование включенное в список", on_delete=models.CASCADE)
    sort_weight = models.IntegerField(default=0, blank=True, help_text="Вес сортировки")

    def __str__(self):
        return "{} , - возраст, {} - пол, {}, {}-sort".format(self.age_client, self.sex_client, self.research, self.sort_weight)

    class Meta:
        unique_together = ("age_client", "sex_client", "research")
        verbose_name = "Диспансеризация Шаблон"
        verbose_name_plural = "Диспансеризация-Шаблоны"


class DispensaryPlan(models.Model):
    research = models.ForeignKey(Researches, db_index=True, blank=True, default=None, null=True, help_text="Исследование включенное в список", on_delete=models.CASCADE)
    repeat = models.PositiveSmallIntegerField(db_index=True, help_text="Кол-во в год", null=False, blank=False)
    diagnos = models.CharField(max_length=511, help_text="Диагноз Д-учета", default="", blank=True, db_index=True)
    speciality = models.ForeignKey(Speciality, db_index=True, blank=True, default=None, null=True, help_text="Профиль-специальности консультации врача", on_delete=models.CASCADE)
    is_visit = models.BooleanField(default=False, blank=True, db_index=True)

    class Meta:
        verbose_name = "Диспансерный учет план"
        verbose_name_plural = "Диспансерный учет"


class ScreeningPlan(models.Model):
    SEX = (
        ("в", "все"),
        ("м", "м"),
        ("ж", "ж"),
    )

    age_start_control = models.PositiveSmallIntegerField(db_index=True, help_text="Возраст начала", validators=[MaxValueValidator(130)])
    age_end_control = models.PositiveSmallIntegerField(db_index=True, help_text="Возраст окончания (включительно)", validators=[MaxValueValidator(130)])
    sex_client = models.CharField(max_length=1, choices=SEX, help_text="Пол", db_index=True)
    research = models.ForeignKey(Researches, db_index=True, help_text="Исследование, включенное в список", on_delete=models.CASCADE)
    period = models.PositiveSmallIntegerField(db_index=True, help_text="Период (1 раз в лет/года)", validators=[MinValueValidator(1), MaxValueValidator(100)])
    sort_weight = models.IntegerField(default=0, blank=True, help_text="Вес сортировки")
    hide = models.BooleanField(default=False, blank=True, help_text="Скрытие", db_index=True)

    def __str__(self):
        return f"{self.age_start_control} - {self.age_end_control} - {self.sex_client}, {self.research}"

    class Meta:
        unique_together = ("age_start_control", "age_end_control", "research", "sex_client")
        verbose_name = "Скрининг Шаблон"
        verbose_name_plural = "Скрининг-Шаблоны"


class GroupCulture(models.Model):
    title = models.CharField(max_length=255, help_text="Группа культур")
    hide = models.BooleanField(default=False, blank=True, help_text="Скрытие группы", db_index=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Группа для культуры"
        verbose_name_plural = "Культуры - группы"

    def as_dict(self):
        return {
            "pk": self.pk,
            "title": self.title,
        }

    @staticmethod
    def get_all_cultures_groups():
        group_culture_obj = GroupCulture.objects.all()
        groups = [{"pk": g.pk, "title": g.title, "hide": g.hide} for g in group_culture_obj]
        return groups

    @staticmethod
    def create_culture_group(title):
        culture_group = GroupCulture(title=title)
        culture_group.save()
        return culture_group

    @staticmethod
    def update_culture_group(pk, title, hide):
        culture_group = GroupCulture.objects.get(pk=pk)
        culture_group.title = title
        culture_group.hide = hide
        culture_group.save()
        return culture_group


class Culture(models.Model):
    title = models.CharField(max_length=255, help_text="Название культуры")
    group_culture = models.ForeignKey(GroupCulture, db_index=True, null=True, blank=True, help_text="Группа для культуры", on_delete=models.SET_NULL)
    fsli = models.CharField(max_length=32, default=None, null=True, blank=True)
    lis = models.CharField(max_length=32, default=None, null=True, blank=True)
    hide = models.BooleanField(default=False, blank=True, help_text="Скрытие культуры", db_index=True)

    def __str__(self):
        return self.title

    def get_full_title(self):
        return f"{self.title}".strip()

    class Meta:
        verbose_name = "Культура"
        verbose_name_plural = "Культуры"

    @staticmethod
    def get_cultures(group):
        if group == "Все" or group == "":
            culture_obj = Culture.objects.all()
        elif group == "Без группы":
            culture_obj = Culture.objects.filter(group_culture=None)
        else:
            culture_obj = Culture.objects.filter(group_culture__title=group)
        elements = []
        for i in culture_obj.order_by("title"):
            title_group = ""
            if i.group_culture:
                title_group = i.group_culture.title
            elements.append({"pk": i.pk, "title": i.title, "fsli": i.fsli, "hide": i.hide, "group": title_group, "lis": i.lis})
        return elements

    @staticmethod
    def culture_save(pk, title="", fsli="", hide=False, lis=""):
        """
        Запись в базу сведений о культуре
        """
        if pk > 0:
            culture_obj = Culture.objects.get(pk=pk)
            culture_obj.title = title
            culture_obj.fsli = fsli
            culture_obj.hide = hide
            culture_obj.lis = lis
        else:
            culture_obj = Culture(title=title, fsli=fsli, hide=hide, group_culture=None, lis=lis)

        culture_obj.save()
        return culture_obj

    @staticmethod
    def culture_update_group(group, elements):
        """
        Запись в базу сведений о культуре
        """
        if group in ["Все", "Без группы"]:
            Culture.objects.filter(pk__in=elements).update(group_culture=None)
        else:
            if isinstance(group, int):
                gr = GroupCulture.objects.get(pk=group)
            else:
                gr = GroupCulture.objects.get(title=group)

            Culture.objects.filter(pk__in=elements).update(group_culture=gr)


class Phenotype(models.Model):
    title = models.CharField(max_length=255, help_text="Название фенотипа")
    fsli = models.CharField(max_length=32, default=None, null=True, blank=True)
    lis = models.CharField(max_length=32, default=None, null=True, blank=True)
    hide = models.BooleanField(default=False, blank=True, help_text="Скрытие фенотипа", db_index=True)

    def __str__(self):
        return self.title

    def get_full_title(self):
        return f"{self.lis} {self.title}".strip()

    class Meta:
        verbose_name = "Фенотип"
        verbose_name_plural = "Фенотипы"


class GroupAntibiotic(models.Model):
    title = models.CharField(max_length=255, help_text="Группа антибиотиков")
    hide = models.BooleanField(default=False, blank=True, help_text="Скрытие группы", db_index=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Группа для антибиотиков"
        verbose_name_plural = "Антибиотики - группы"

    def as_dict(self):
        return {
            "pk": self.pk,
            "title": self.title,
        }

    @staticmethod
    def get_all_antibiotic_groups():
        group_antibiotic_obj = GroupAntibiotic.objects.all()
        groups = [{"pk": g.pk, "title": g.title, "hide": g.hide} for g in group_antibiotic_obj]
        return groups

    @staticmethod
    def create_antibiotic_group(title):
        antibiotic_group = GroupAntibiotic(title=title)
        antibiotic_group.save()
        return antibiotic_group

    @staticmethod
    def update_antibiotic_group(pk, title, hide):
        antibiotic_group = GroupAntibiotic.objects.get(pk=pk)
        antibiotic_group.title = title
        antibiotic_group.hide = hide
        antibiotic_group.save()
        return antibiotic_group


class Antibiotic(models.Model):
    title = models.CharField(max_length=255, help_text="Название антибиотика")
    group_antibiotic = models.ForeignKey(GroupAntibiotic, db_index=True, null=True, blank=True, help_text="Группа антибиотиков", on_delete=models.SET_NULL)
    fsli = models.CharField(max_length=32, default=None, null=True, blank=True)
    lis = models.CharField(max_length=32, default=None, null=True, blank=True)
    hide = models.BooleanField(default=False, blank=True, help_text="Скрытие антибиотика", db_index=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Антибиотик"
        verbose_name_plural = "Антибиотики"

    def as_dict(self):
        return {
            "pk": self.pk,
            "title": self.title,
        }

    @staticmethod
    def get_antibiotics(group):
        if group == "Все" or group == "":
            antibiotic_obj = Antibiotic.objects.all()
        elif group == "Без группы":
            antibiotic_obj = Antibiotic.objects.filter(group_antibiotic=None)
        else:
            antibiotic_obj = Antibiotic.objects.filter(group_antibiotic__title=group)
        elements = []
        for i in antibiotic_obj.order_by("title"):
            title_group = ""
            if i.group_antibiotic:
                title_group = i.group_antibiotic.title
            elements.append({"pk": i.pk, "title": i.title, "fsli": i.fsli, "hide": i.hide, "group": title_group, "lis": i.lis})
        return elements

    @staticmethod
    def antibiotic_save(pk, title="", fsli="", hide=False, lis=""):
        if pk > 0:
            antibiotic_obj = Antibiotic.objects.get(pk=pk)
            antibiotic_obj.title = title
            antibiotic_obj.fsli = fsli
            antibiotic_obj.hide = hide
            antibiotic_obj.lis = lis
        else:
            antibiotic_obj = Antibiotic(title=title, fsli=fsli, hide=hide, group_antibiotic=None, lis=lis)
        antibiotic_obj.save()
        return antibiotic_obj

    @staticmethod
    def antibiotic_update_group(group, elements):
        if group == "Все":
            return ""

        if group == "Без группы":
            Antibiotic.objects.filter(pk__in=elements).update(group_antibiotic=None)
        else:
            if isinstance(group, int):
                gr = GroupAntibiotic.objects.get(pk=group)
            else:
                gr = GroupAntibiotic.objects.get(title=group)
            Antibiotic.objects.filter(pk__in=elements).update(group_antibiotic=gr)


class AntibioticSets(models.Model):
    title = models.CharField(max_length=255, help_text="Название антибиотика")
    antibiotics = models.ManyToManyField(Antibiotic)
    hide = models.BooleanField(default=False, blank=True, help_text="Скрытие набора", db_index=True)

    def __str__(self):
        return self.title

    def as_dict(self):
        return {
            "pk": self.pk,
            "title": self.title,
        }

    class Meta:
        verbose_name = "Антибиотик - Наборы"
        verbose_name_plural = "Антибиотики - Наборы"

    def get_not_hidden_antibiotics(self):
        return self.antibiotics.filter(hide=False)

    @staticmethod
    def create_antibiotic_set(title):
        antibiotic_set = AntibioticSets(title=title)
        antibiotic_set.save()
        return antibiotic_set

    @staticmethod
    def update_antibiotic_set(pk, title, hide):
        antibiotic_set = AntibioticSets.objects.get(pk=pk)
        antibiotic_set.title = title
        antibiotic_set.hide = hide
        antibiotic_set.save()
        return antibiotic_set

    @staticmethod
    def get_antibiotic_set():
        antibiotic_set = AntibioticSets.objects.all().order_by("title")
        sets = [{"pk": i.pk, "title": i.title, "hide": i.hide} for i in antibiotic_set]
        return sets

    @staticmethod
    def get_antibiotic_set_elements(title):
        elements = None
        if title:
            set_obj = AntibioticSets.objects.get(title=title)
            antibiotic_obj = set_obj.antibiotics.all().order_by("title")
            elements = [{"pk": i.pk, "title": i.title, "hide": i.hide} for i in antibiotic_obj]

        return elements

    @staticmethod
    def update_antibiotic_set_elements(group, elements):
        if group and elements:
            gr = AntibioticSets.objects.get(title=group)
            if gr.pk > 0:
                set_obj = AntibioticSets.objects.get(title=group)
                element_ant = Antibiotic.objects.filter(pk__in=elements)
                set_obj.antibiotics.clear()
                set_obj.antibiotics.add(*element_ant)

        return elements


class SetResearch(models.Model):
    title = models.CharField(max_length=255, help_text="Название набора")
    hide = models.BooleanField(default=False, blank=True, help_text="Скрыть", db_index=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Набор исследований"
        verbose_name_plural = "Наборы исследований"


class SetOrderResearch(models.Model):
    set_research = models.ForeignKey(SetResearch, default=None, help_text="Набор", db_index=True, on_delete=models.CASCADE)
    research = models.ForeignKey(Researches, default=None, help_text="Исследование", db_index=True, on_delete=models.CASCADE)
    order = models.IntegerField(help_text="Порядок")

    class Meta:
        verbose_name = "Исследование в наборе"
        verbose_name_plural = "Исследования в наборе"
