from django.db import models
from podrazdeleniya.models import Podrazdeleniya
from jsonfield import JSONField
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


class Researches(models.Model):
    """
    Вид исследования
    """
    DIRECTION_FORMS = (
        (0, 'По умолчанию'),

        (38001, '38001. ИО - Направление на ВИЧ'),
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
    need_vich_code = models.BooleanField(default=False, blank=True, help_text="Необходимость указания кода вич в направлении")
    paraclinic_info = models.TextField(blank=True, default="", help_text="Если это параклиническое исследование - здесь указывается подготовка и кабинет")
    instructions = models.TextField(blank=True, default="", help_text="Памятка для направления")
    not_grouping = models.BooleanField(default=False, blank=True, help_text="Нельзя группировать в направления?")
    direction_form = models.IntegerField(default=0, blank=True, choices=DIRECTION_FORMS, help_text="Форма направления")

    def __str__(self):
        return "%s (Лаб. %s, Скрыт=%s)" % (self.title, self.podrazdeleniye, self.hide)

    def get_podrazdeleniye(self):
        return self.podrazdeleniye

    def get_title(self):
        return self.short_title if self.short_title != '' else self.title

    def get_full_short_title(self):
        return self.title if self.get_title() == self.title else "{} ({})".format(self.title, self.get_title())

    class Meta:
        verbose_name = 'Вид исследования'
        verbose_name_plural = 'Виды исследований'


class ParaclinicInputGroups(models.Model):
    title = models.CharField(max_length=255, help_text='Название группы')
    show_title = models.BooleanField()
    research = models.ForeignKey(Researches, on_delete=models.CASCADE)
    order = models.IntegerField()
    hide = models.BooleanField()


class ParaclinicInputField(models.Model):
    title = models.CharField(max_length=255, help_text='Название поля ввода')
    group = models.ForeignKey(ParaclinicInputGroups, on_delete=models.CASCADE)
    order = models.IntegerField()
    default_value = models.TextField()
    input_templates = models.TextField()
    hide = models.BooleanField()
    lines = models.IntegerField(default=3)


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
    uet_doc = models.FloatField(default=0, help_text='УЕТы для врача', blank=True)
    uet_lab = models.FloatField(default=0, help_text='УЕТы для лаборанта', blank=True)
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

class RouteSheet(models.Model):
    name_route_sheet = models.ForeignKey(NameRouteSheet, db_index=True, help_text='Наименование перечня',on_delete=models.CASCADE)
    research = models.ForeignKey(Researches, db_index=True, help_text='Исследование включенное в список',
                                 on_delete=models.CASCADE)
    work_time = models.CharField(max_length=55, help_text='Время работы', blank=True, default='')
    cabinet = models.CharField(max_length=25, help_text='кабинет', blank=True, default='')
    comment = models.TextField(max_length=255, help_text='Комментарий', blank=True, default='')

    def __str__(self):
        return "{} , - исследование {}".format(self.name_route_sheet, self.research)


    class Meta:
        verbose_name = 'Списоки маршрутов - Услуги'
        verbose_name_plural = 'Списки маршрутов - Услуги'
