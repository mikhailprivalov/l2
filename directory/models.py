from django.db import models, transaction
from jsonfield import JSONField

from podrazdeleniya.models import Podrazdeleniya
from researches.models import Tubes


class DirectionsGroup(models.Model):
    """
    Группы направлений
    """
    pass

    class Meta:
        verbose_name = 'Группа направлений'
        verbose_name_plural = 'Группы направлений'


class ReleationsFT(models.Model):
    """
    (многие-ко-многим) фракции к пробиркам
    """
    tube = models.ForeignKey(Tubes, help_text='Ёмкость', db_index=True, on_delete=models.CASCADE)
    receive_in_lab = models.BooleanField(default=False, blank=True, help_text="Приём пробирки в лаборатории разрешён без подтверждения забора")

    def __str__(self):
        return "%d %s" % (self.pk, self.tube.title)

    class Meta:
        verbose_name = 'Физическая пробирка для фракций'
        verbose_name_plural = 'Физические пробирки для фракций'


class ResearchGroup(models.Model):
    """
    Группы исследований
    """
    title = models.CharField(max_length=63, help_text='Название группы')
    lab = models.ForeignKey(Podrazdeleniya, null=True, blank=True, help_text='Лаборатория', db_index=True, on_delete=models.CASCADE)

    def __str__(self):
        return "%s" % self.title

    class Meta:
        verbose_name = 'Группа исследований'
        verbose_name_plural = 'Группы исследований'


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
        (0, 'Консультация врача'),
        (1, 'Лечение'),
        (2, 'Стоматалогия'),
        (3, 'Стационар'),
        (4, 'Микробиология'),
    )

    site_type = models.SmallIntegerField(choices=TYPES, help_text="Тип раздела", db_index=True)
    title = models.CharField(max_length=255, help_text='Подраздел')
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие подраздела', db_index=True)

    def __str__(self):
        return "%s" % self.title

    class Meta:
        verbose_name = 'Подраздел'
        verbose_name_plural = 'Подразделы'


class Localization(models.Model):
    title = models.CharField(max_length=64, help_text="Название места локализации")
    fsli = models.CharField(max_length=32, default=None, null=True, blank=True)
    barcode = models.CharField(max_length=15, default="", blank=True)

    def __str__(self):
        return "%s" % self.title

    class Meta:
        verbose_name = 'Локализация'
        verbose_name_plural = 'Локализации'


class ServiceLocation(models.Model):
    title = models.CharField(max_length=64, help_text="Название места оказания услуги")
    hide = models.BooleanField(help_text="Скрытие")

    def __str__(self):
        return "%s" % self.title

    class Meta:
        verbose_name = 'Место оказания услуги'
        verbose_name_plural = 'Места оказания услуг'


class Researches(models.Model):
    """
    Вид исследования
    """
    DIRECTION_FORMS = (
        (0, 'По умолчанию'),

        (38001, '38001. ИО - Направление на ВИЧ'),
        (38002, '38002. ИО - Направление на МСКТ'),
        (38003, '38003. ИО - Направление на COVID-19'),
    )

    CO_EXECUTOR_MODES = (
        (0, 'Нет'),
        (1, '1 со-исполнитель'),
        (2, '2 со-исполнителя'),
    )

    direction = models.ForeignKey(DirectionsGroup, null=True, blank=True, help_text='Группа направления', on_delete=models.SET_NULL)
    title = models.CharField(max_length=255, default="", help_text='Название исследования')
    short_title = models.CharField(max_length=255, default='', blank=True)
    podrazdeleniye = models.ForeignKey(Podrazdeleniya, related_name="department", help_text="Лаборатория", db_index=True, null=True, blank=True, default=None, on_delete=models.CASCADE)
    quota_oms = models.IntegerField(default=-1, help_text='Квота по ОМС', blank=True)
    preparation = models.CharField(max_length=2047, default="", help_text='Подготовка к исследованию', blank=True)
    edit_mode = models.IntegerField(default=0, help_text='0 - Лаборант может сохранять и подтверждать. 1 - Лаборант сохраняет, врач должен подтвердить')
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие исследования', db_index=True)
    no_units_and_ref = models.BooleanField(default=False, blank=True,
                                           help_text='На бланке результата скрытие единиц измерения и референсов')
    no_attach = models.IntegerField(default=0, null=True, blank=True,
                                    help_text='Группа исследований, которые не могут быть назначены вместе')
    sort_weight = models.IntegerField(default=0, null=True, blank=True, help_text='Вес сортировки')
    template = models.IntegerField(default=0, blank=True, help_text='Шаблон формы')
    comment_variants = models.ForeignKey("directory.MaterialVariants", default=None, null=True, blank=True, help_text='Варианты комментариев к материалу', on_delete=models.SET_NULL)
    groups = models.ManyToManyField(ResearchGroup, blank=True, help_text='Группа исследований в лаборатории', db_index=True)
    onlywith = models.ForeignKey('self', null=True, blank=True, help_text='Без выбранного анализа не можеть быть назначено', on_delete=models.SET_NULL)
    can_lab_result_comment = models.BooleanField(default=False, blank=True, help_text='Возможность оставить комментарий лабораторией')
    code = models.TextField(default='', blank=True, help_text='Код исследования (несколько кодов разделяются точкой с запятой без пробелов)')
    is_paraclinic = models.BooleanField(default=False, blank=True, help_text="Это параклиническое исследование?")
    is_doc_refferal = models.BooleanField(default=False, blank=True, help_text="Это исследование-направление к врачу")
    is_treatment = models.BooleanField(default=False, blank=True, help_text="Это лечение")
    is_stom = models.BooleanField(default=False, blank=True, help_text="Это стоматология")
    is_hospital = models.BooleanField(default=False, blank=True, help_text="Это стационар")
    is_slave_hospital = models.BooleanField(default=False, blank=True, help_text="Это стационарный протокол")
    is_microbiology = models.BooleanField(default=False, blank=True, help_text="Это микробиологическое исследование")
    site_type = models.ForeignKey(ResearchSite, default=None, null=True, blank=True, help_text='Место услуги', on_delete=models.SET_NULL, db_index=True)

    need_vich_code = models.BooleanField(default=False, blank=True, help_text="Необходимость указания кода вич в направлении")
    paraclinic_info = models.TextField(blank=True, default="", help_text="Если это параклиническое исследование - здесь указывается подготовка и кабинет")
    instructions = models.TextField(blank=True, default="", help_text="Памятка для направления")
    not_grouping = models.BooleanField(default=False, blank=True, help_text="Нельзя группировать в направления?")
    direction_form = models.IntegerField(default=0, blank=True, choices=DIRECTION_FORMS, help_text="Форма направления")
    def_discount = models.SmallIntegerField(default=0, blank=True, help_text="Размер скидки")
    prior_discount = models.BooleanField(default=False, blank=True, help_text="Приоритет скидки")
    is_first_reception = models.BooleanField(default=False, blank=True, help_text="Эта услуга - первичный прием")
    internal_code = models.CharField(max_length=255, default="", help_text='Внутренний код исследования', blank=True)
    co_executor_mode = models.SmallIntegerField(default=0, choices=CO_EXECUTOR_MODES, blank=True)
    co_executor_2_title = models.CharField(max_length=40, default='Со-исполнитель', blank=True)
    microbiology_tube = models.ForeignKey(Tubes, blank=True, default=None, null=True,
                                          help_text="Пробирка для микробиологического исследования",
                                          on_delete=models.SET_NULL)
    localization = models.ManyToManyField(Localization, blank=True, default=None, help_text="Возможная локализация")
    service_location = models.ManyToManyField(ServiceLocation, blank=True, default=None, help_text="Возможные места оказаний")
    wide_headers = models.BooleanField(blank=True, default=False, help_text="Заголовки полей ввода на всю страницу")
    auto_add_hidden = models.ManyToManyField('directory.Researches', related_name="res_auto_add_hidden", default=None, blank=True,
                                             help_text="Автоматически добавляемые назначения (не отображается в интерфейсе)")
    vertical_result_display = models.BooleanField(blank=True, default=False, help_text="Отображение дат лабораторных тестов вертикально")

    @staticmethod
    def filter_type(t):
        ts = {
            4: dict(is_paraclinic=True),
            5: dict(is_doc_refferal=True),
            6: dict(is_treatment=True),
            7: dict(is_stom=True),
            8: dict(is_hospital=True),
            9: dict(is_microbiology=True),
        }
        return ts.get(t, {})

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
        if self.is_microbiology:
            return -6
        return self.podrazdeleniye_id or -2

    @property
    def desc(self):
        return self.is_treatment or self.is_stom or self.is_doc_refferal or self.is_paraclinic or self.is_microbiology or self.is_hospital

    @property
    def can_transfer(self):
        if self.desc:
            return False
        return 'перевод' in self.title.lower()

    @property
    def is_extract(self):
        if self.desc:
            return False
        return 'выписка' in self.title.lower() or 'выписной' in self.title.lower()

    @property
    def r_type(self):
        if self.is_paraclinic:
            return "is_paraclinic"

        if self.is_doc_referral:
            return "consultation"

        hs = HospitalService.objects.filter(slave_research=self).first()

        if hs:
            return HospitalService.TYPES_BY_KEYS_REVERSED.get(hs.site_type, 'None')

        if self.podrazdeleniye and self.podrazdeleniye.p_type == Podrazdeleniya.LABORATORY:
            return "laboratory"

        return "None"

    def __str__(self):
        return "%s (Лаб. %s, Скрыт=%s)" % (self.title, self.podrazdeleniye, self.hide)

    def get_podrazdeleniye(self):
        return self.podrazdeleniye

    def get_title(self):
        return self.short_title if self.short_title != '' else self.title

    def get_full_short_title(self):
        return self.title if self.get_title() == self.title else "{} ({})".format(self.title, self.get_title())

    def get_full_short_title_concat(self):
        if self.get_title() == self.title:
            return self.title
        return f'{self.title} – {self.short_title}'

    class Meta:
        verbose_name = 'Вид исследования'
        verbose_name_plural = 'Виды исследований'


class HospitalService(models.Model):
    TYPES = (
        (0, 'Первичный прием'),
        (1, 'Дневник'),
        (2, 'ВК'),
        (3, 'Операция'),
        (4, 'Фармакотерапия'),
        (5, 'Физиотерапия'),
        (6, 'Эпикриз'),
        (7, 'Выписка'),
        (8, 'Больничный лист'),
        (9, 't, ad, p – лист'),
    )

    TYPES_BY_KEYS = {
        'primary receptions': 0,
        'diaries': 1,
        'vc': 2,
        'operation': 3,
        'pharmacotherapy': 4,
        'physiotherapy': 5,
        'epicrisis': 6,
        'extracts': 7,
        'bl': 8,
        't, ad, p sheet': 9,
    }

    TYPES_BY_KEYS_REVERSED = {
        0: 'primary receptions',
        1: 'diaries',
        2: 'vc',
        3: 'operation',
        4: 'pharmacotherapy',
        5: 'physiotherapy',
        6: 'epicrisis',
        7: 'extracts',
        8: 'bl',
        9: 't, ad, p sheet',
    }

    TYPES_REVERSED = {
        "paraclinical": "is_paraclinic",
        "laboratory": "is_lab",
        "consultation": "is_doc_refferal",
        "diaries": "diaries",
        "all": "None",
    }

    main_research = models.ForeignKey(Researches, help_text="Стационарная услуга", on_delete=models.CASCADE,
                                      db_index=True)
    site_type = models.SmallIntegerField(choices=TYPES, help_text="Тип подраздела в стационарной карте", db_index=True)
    slave_research = models.ForeignKey(Researches, related_name='research_protocol',
                                       help_text="Протокол для вида услуги", on_delete=models.CASCADE)
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие услуги', db_index=True)

    def get_title(self):
        return f"{self.main_research.title} – {self.slave_research.get_full_short_title_concat()}"

    def __str__(self):
        return f"{self.main_research.title} - {self.site_type} - {self.slave_research.title} - {self.hide}"

    class Meta:
        verbose_name = 'Стационарная услуга'
        verbose_name_plural = 'Стационарные услуги'


class ParaclinicInputGroups(models.Model):
    title = models.CharField(max_length=255, help_text='Название группы')
    show_title = models.BooleanField()
    research = models.ForeignKey(Researches, on_delete=models.CASCADE)
    order = models.IntegerField()
    hide = models.BooleanField()
    visibility = models.TextField(default='', blank=True)


class ParaclinicInputField(models.Model):
    TYPES = (
        (0, 'Text'),
        (1, 'Date'),
        (2, 'MKB'),
        (3, 'Calc'),
        (4, 'purpose'),
        (5, 'first_time'),
        (6, 'result_reception'),
        (7, 'outcome_illness'),
        (8, 'maybe_onco'),
        (9, 'List'),
        (10, 'Dict'),
        (11, 'Fraction'),
        (12, 'Radio'),
        (13, 'Protocol field'),
        (14, 'Protocol raw field'),
        (15, 'Rich text'),
        (16, 'Agg lab'),
        (17, 'Agg desc'),
        (18, 'Number'),
        (19, 'Number range'),
        (20, 'Time HH:MM'),
        (21, 'Anesthesia table'),
        (22, 'Текст с автозаполнением'),
    )

    title = models.CharField(max_length=400, help_text='Название поля ввода')
    group = models.ForeignKey(ParaclinicInputGroups, on_delete=models.CASCADE)
    order = models.IntegerField()
    default_value = models.TextField(blank=True, default='')
    input_templates = models.TextField()
    hide = models.BooleanField()
    lines = models.IntegerField(default=3)
    field_type = models.SmallIntegerField(default=0, choices=TYPES, blank=True)
    required = models.BooleanField(default=False, blank=True)
    for_talon = models.BooleanField(default=False, blank=True)
    visibility = models.TextField(default='', blank=True)
    helper = models.CharField(max_length=999, blank=True, default='')
    for_extract_card = models.BooleanField(default=False, help_text='В выписку', blank=True)

    def get_title(self, force_type=None, recursive=False):
        field_type = force_type or self.field_type
        titles = ['']
        if self.title:
            titles.append(self.title)
        if field_type != 14:
            if field_type == 11 and Fractions.objects.filter(pk=self.default_value).exists():
                f = Fractions.objects.get(pk=self.default_value)
                titles.append(f.research.title)
                if f.title not in titles:
                    titles[-1] = titles[-1] + ' – ' + f.title
            if field_type == 13 and ParaclinicInputField.objects.filter(pk=self.default_value).exists():
                f = ParaclinicInputField.objects.get(pk=self.default_value)
                titles.append(f.group.research.title)
                gt = f.group.title
                if gt not in titles:
                    titles[-1] = titles[-1] + ' – ' + gt
                ft = f.get_title(recursive=True)
                if ft not in titles and not recursive:
                    titles[-1] = titles[-1] + ' – ' + ft
        title = ', '.join([t for t in titles if t])
        return title


class ParaclinicTemplateName(models.Model):
    DEFAULT_TEMPLATE_TITLE = 'По умолчанию'

    title = models.CharField(max_length=255, help_text='Название шаблона запонение полей')
    research = models.ForeignKey(Researches, on_delete=models.CASCADE, db_index=True)
    hide = models.BooleanField(default=False, blank=True, help_text="Скрыть шаблон")

    def __str__(self):
        return "%s (Лаб. %s, Скрыт=%s)" % (self.title, self.research, self.hide)

    @staticmethod
    def make_default(research: Researches) -> 'ParaclinicTemplateName':
        if not ParaclinicTemplateName.objects.filter(research=research,
                                                     title=ParaclinicTemplateName.DEFAULT_TEMPLATE_TITLE).exists():
            with transaction.atomic():
                p = ParaclinicTemplateName(research=research,
                                           title=ParaclinicTemplateName.DEFAULT_TEMPLATE_TITLE)
                p.save()
                for f in ParaclinicInputField.objects.filter(group__research=research):
                    ParaclinicTemplateField(template_name=p, input_field=f, value=f.default_value).save()
        return ParaclinicTemplateName.objects.get(research=research,
                                                  title=ParaclinicTemplateName.DEFAULT_TEMPLATE_TITLE)


class ParaclinicTemplateField(models.Model):
    template_name = models.ForeignKey(ParaclinicTemplateName, on_delete=models.CASCADE, db_index=True)
    input_field = models.ForeignKey(ParaclinicInputField, on_delete=models.CASCADE)
    value = models.TextField(help_text='Значение')

    def __str__(self):
        return "%s (Лаб. %s, Скрыт=%s)" % (self.template_name, self.input_field.title, self.value)


class AutoAdd(models.Model):
    """
    Перечисление связей исследований, которые могут быть назначены только вместе (A только с B)
    """
    a = models.ForeignKey(Researches, help_text="Исследование, для которого устанавливается связь", db_index=True, related_name="a", on_delete=models.CASCADE)
    b = models.ForeignKey(Researches, help_text="Исследование, которое должно быть назначено вместе", related_name="b", on_delete=models.CASCADE)

    def __str__(self):
        return "%s -> %s" % (self.a.title, self.b.title)

    class Meta:
        verbose_name = 'Автоматическое добавление назначений'
        verbose_name_plural = 'Автоматическоие добавления назначений'


class References(models.Model):
    """
    Справочник референсов
    """
    title = models.CharField(max_length=255, help_text='Название')
    about = models.TextField(help_text='Описание', blank=True)
    ref_m = JSONField(help_text='М')
    ref_f = JSONField(help_text='Ж')
    fraction = models.ForeignKey("Fractions", db_index=True, help_text='Фракция, к которой относится референс', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.fraction) + " | " + str(self.fraction) + " | " + self.title

    class Meta:
        verbose_name = 'Референс'
        verbose_name_plural = 'Референсы'


class ResultVariants(models.Model):
    values = models.TextField(
        help_text='Варианты подсказок результатов, перечисленные через вертикальную черту без пробела "|"')

    def get_variants(self):
        return self.values.split('|')

    def __str__(self):
        return str(self.get_variants())

    class Meta:
        verbose_name = 'Вариант результата'
        verbose_name_plural = 'Варианты результатов'


class MaterialVariants(models.Model):
    values = models.TextField(
        help_text='Варианты комментариев для материала, перечисленные через вертикальную черту без пробела "|"')

    def get_variants(self):
        return self.values.split('|')

    def __str__(self):
        return str(self.get_variants())

    class Meta:
        verbose_name = 'Вариант комментария'
        verbose_name_plural = 'Варианты комментариев'


# class Units(models.Model):
#     title = models.CharField(max_length=40, help_text="Единицы измерения")
#
#
#
# class SharedParameters(models.Model):
#     title = models.CharField(max_length=255, help_text='Название параметра')


class Fractions(models.Model):
    """
    Фракции для исследований
    """
    title = models.CharField(max_length=255, help_text='Название фракции')
    research = models.ForeignKey(Researches, db_index=True, help_text='Исследование, к которому относится фракция', on_delete=models.CASCADE)
    units = models.CharField(max_length=255, help_text='Еденицы измерения', blank=True, default='')
    default_ref = models.ForeignKey(References, help_text='Референс по-умолчанию', blank=True, null=True, default=None, on_delete=models.SET_NULL)
    ref_m = JSONField(help_text='Референсы (М)', blank=True, default="{}")
    ref_f = JSONField(help_text='Референсы (Ж)', blank=True, default="{}")
    relation = models.ForeignKey(ReleationsFT, help_text='Пробирка (пробирки)', db_index=True, on_delete=models.CASCADE, null=True, default=None, blank=True)
    uet_doc = models.FloatField(default=0, help_text='УЕТы врача', blank=True)
    uet_co_executor_1 = models.FloatField(default=0, help_text='УЕТы со-исполнителя 1', blank=True)
    uet_co_executor_2 = models.FloatField(default=0, help_text='УЕТы со-исполнителя 2', blank=True)
    max_iterations = models.IntegerField(default=1, help_text='Максимальное число итераций', blank=True)
    variants = models.ForeignKey(ResultVariants, null=True, blank=True, help_text='Варианты подсказок результатов', on_delete=models.SET_NULL)
    variants2 = models.ForeignKey(ResultVariants, related_name="variants2", null=True, blank=True, help_text='Варианты подсказок результатов для Бак.лаб.', on_delete=models.SET_NULL)
    sort_weight = models.IntegerField(default=0, null=True, blank=True, help_text='Вес соритировки')
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие фракции', db_index=True)
    render_type = models.IntegerField(default=0, blank=True, help_text='Тип рендеринга (базовый тип (0) или динамическое число полей (1)')
    options = models.CharField(max_length=511, default="", blank=True, help_text='Варианты для динамического числа полей')
    formula = models.TextField(default="", blank=True, help_text="Формула для автоматического вычисления значения")
    code = models.CharField(max_length=16, default='', blank=True, help_text='Код фракции')
    print_title = models.BooleanField(default=False, blank=True, help_text='Печатать название(Группировка)', db_index=True)
    readonly_title = models.BooleanField(default=False, blank=True,
                                         help_text='Только для чтения-суррогатная группа для фракций', db_index=True)
    fsli = models.CharField(max_length=32, default=None, null=True, blank=True)

    def __str__(self):
        return self.research.title + " | " + self.title

    class Meta:
        verbose_name = 'Фракция'
        verbose_name_plural = 'Фракции'


class Absorption(models.Model):
    """
    Поглощение
    """
    fupper = models.ForeignKey(Fractions, related_name="fupper", help_text='Какая фракция главнее', db_index=True, on_delete=models.CASCADE)
    flower = models.ForeignKey(Fractions, related_name="flower", help_text='Какая фракция поглащяется главной', on_delete=models.CASCADE)

    def __str__(self):
        return self.flower.__str__() + " -> " + self.fupper.__str__()

    class Meta:
        verbose_name = 'Поглощение фракции'
        verbose_name_plural = 'Поглощения фракций'


class NameRouteSheet(models.Model):
    """
    Route list for research. Маршрутный лист для исследований
    """
    title = models.CharField(max_length=255, unique=True, help_text='Название маршрутного листа')
    static_text = models.TextField(default="", help_text='Текст перед списком')

    def __str__(self):
        return "{}".format(self.title)

    def get_title(self):
        return self.title

    class Meta:
        verbose_name = 'Cписки маршрутов'
        verbose_name_plural = 'Списки маршрутов'


class DispensaryRouteSheet(models.Model):
    SEX = (
        ('м', 'м'),
        ('ж', 'ж'),
    )

    age_client = models.PositiveSmallIntegerField(db_index=True, help_text='Возраст', null=False, blank=False)
    sex_client = models.CharField(max_length=1, choices=SEX, help_text="Пол", db_index=True)
    research = models.ForeignKey(Researches, db_index=True, help_text='Исследование включенное в список',
                                 on_delete=models.CASCADE)
    sort_weight = models.IntegerField(default=0, blank=True, help_text='Вес соритировки')

    def __str__(self):
        return "{} , - возраст, {} - пол, {}, {}-sort".format(self.age_client, self.sex_client, self.research, self.sort_weight)

    class Meta:
        unique_together = ("age_client", "sex_client", "research")
        verbose_name = 'Диспансеризация Шаблон'
        verbose_name_plural = 'Диспансеризация-Шаблоны'


class GroupCulture(models.Model):
    title = models.CharField(max_length=255, help_text="Группа культур")
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие группы', db_index=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Группа для культуры'
        verbose_name_plural = 'Культуры - группы'

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
    group_culture = models.ForeignKey(GroupCulture, db_index=True, null=True, blank=True, help_text='Группа для культуры', on_delete=models.SET_NULL)
    fsli = models.CharField(max_length=32, default=None, null=True, blank=True)
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие культуры', db_index=True)

    def __str__(self):
        return self.title

    def get_full_title(self):
        return f'{self.group_culture.title} {self.title}'.strip()

    class Meta:
        verbose_name = 'Культура'
        verbose_name_plural = 'Культуры'

    @staticmethod
    def get_cultures(group):
        if group == "Все" or group == '':
            culture_obj = Culture.objects.all()
        elif group == "Без группы":
            culture_obj = Culture.objects.filter(group_culture=None)
        else:
            culture_obj = Culture.objects.filter(group_culture__title=group)
        elements = []
        for i in culture_obj.order_by('title'):
            title_group = ""
            if i.group_culture:
                title_group = i.group_culture.title
            elements.append({"pk": i.pk, "title": i.title, "fsli": i.fsli, "hide": i.hide, "group": title_group})
        return elements

    @staticmethod
    def culture_save(pk, title='', fsli='', hide=False):
        """
        Запись в базу сведений о культуре
        """
        if pk > 0:
            culture_obj = Culture.objects.get(pk=pk)
            culture_obj.title = title
            culture_obj.fsli = fsli
            culture_obj.hide = hide
        else:
            culture_obj = Culture(title=title, fsli=fsli, hide=hide, group_culture=None)

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


class GroupAntibiotic(models.Model):
    title = models.CharField(max_length=255, help_text="Группа антибиотиков")
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие группы', db_index=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Группа для антибиотиков'
        verbose_name_plural = 'Антибиотики - группы'

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
    group_antibiotic = models.ForeignKey(GroupAntibiotic, db_index=True, null=True, blank=True, help_text='Группа антибиотиков', on_delete=models.SET_NULL)
    fsli = models.CharField(max_length=32, default=None, null=True, blank=True)
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие антибиотика', db_index=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Антибиотик'
        verbose_name_plural = 'Антибиотики'

    def as_dict(self):
        return {
            "pk": self.pk,
            "title": self.title,
        }

    @staticmethod
    def get_antibiotics(group):
        if group == "Все" or group == '':
            antibiotic_obj = Antibiotic.objects.all()
        elif group == "Без группы":
            antibiotic_obj = Antibiotic.objects.filter(group_antibiotic=None)
        else:
            antibiotic_obj = Antibiotic.objects.filter(group_antibiotic__title=group)
        elements = []
        for i in antibiotic_obj.order_by('title'):
            title_group = ""
            if i.group_antibiotic:
                title_group = i.group_antibiotic.title
            elements.append({"pk": i.pk, "title": i.title, "fsli": i.fsli, "hide": i.hide, "group": title_group})
        return elements

    @staticmethod
    def antibiotic_save(pk, title='', fsli='', hide=False):
        if pk > 0:
            antibiotic_obj = Antibiotic.objects.get(pk=pk)
            antibiotic_obj.title = title
            antibiotic_obj.fsli = fsli
            antibiotic_obj.hide = hide
        else:
            antibiotic_obj = Antibiotic(title=title, fsli=fsli, hide=hide, group_antibiotic=None)
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
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие набора', db_index=True)

    def __str__(self):
        return self.title

    def as_dict(self):
        return {
            "pk": self.pk,
            "title": self.title,
        }

    class Meta:
        verbose_name = 'Антибиотик - Наборы'
        verbose_name_plural = 'Антибиотики - Наборы'

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
        antibiotic_set = AntibioticSets.objects.all().order_by('title')
        sets = [{"pk": i.pk, "title": i.title, "hide": i.hide} for i in antibiotic_set]
        return sets

    @staticmethod
    def get_antibiotic_set_elements(title):
        elements = None
        if title:
            set_obj = AntibioticSets.objects.get(title=title)
            antibiotic_obj = set_obj.antibiotics.all().order_by('title')
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
