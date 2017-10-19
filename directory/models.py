from django.db import models
from podrazdeleniya.models import Subgroups, Podrazdeleniya
from jsonfield import JSONField
from researches.models import Tubes
from users.models import DoctorProfile


class DirectionsGroup(models.Model):
    """
    Группы направлений
    """
    pass


class ReleationsFT(models.Model):
    """
    (многие-ко-многим) фракции к пробиркам
    """
    tube = models.ForeignKey(Tubes, help_text='Пробирка', db_index=True)
    receive_in_lab = models.BooleanField(default=False, blank=True, help_text="Приём пробирки в лаборатории разрешён без подтверждения забора")

    def __str__(self):
        return "%d %s" % (self.pk, self.tube.title)


class ResearchGroup(models.Model):
    """
    Группы исследований
    """
    title = models.CharField(max_length=63, help_text='Название группы')
    lab = models.ForeignKey(Podrazdeleniya, null=True, blank=True, help_text='Лаборатория')

    def __str__(self):
        return "%s" % self.title


class Researches(models.Model):
    """
    Вид исследования
    """
    direction = models.ForeignKey(DirectionsGroup, null=True, blank=True, help_text='Группа направления')
    title = models.CharField(max_length=255, default="", help_text='Название исследования')
    subgroup = models.ForeignKey(Subgroups, related_name="subgroup", help_text='Подгруппа в лаборатории', db_index=True)
    quota_oms = models.IntegerField(default=-1, help_text='Квота по ОМС')
    preparation = models.CharField(max_length=2047, default="", help_text='Подготовка к исследованию')
    edit_mode = models.IntegerField(
        default=0,
        help_text='0 - Лаборант может сохранять и подтверждать. 1 - Лаборант сохраняет, врач должен подтвердить')
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие исследования', db_index=True)
    no_attach = models.IntegerField(default=0, null=True, blank=True,
                                    help_text='Группа исследований, которые не могут быть назначены вместе')
    sort_weight = models.IntegerField(default=0, null=True, blank=True, help_text='Вес сортировки')
    template = models.IntegerField(default=0, blank=True, help_text='Шаблон формы')
    comment_template = models.IntegerField(default=-1, null=True, blank=True,
                                           help_text='Варианты комментариев к материалу (deprecated)')
    comment_variants = models.ForeignKey("directory.MaterialVariants", default=None, null=True, blank=True, help_text='Варианты комментариев к материалу')
    groups = models.ManyToManyField(ResearchGroup, blank=True, help_text='Группа исследований в лаборатории')
    onlywith = models.ForeignKey('self', null=True, blank=True,
                                 help_text='Без выбранного анализа не можеть быть назначено')
    can_lab_result_comment = models.BooleanField(default=False, blank=True,
                                                 help_text='Возможность оставить комментарий лабораторией')
    code = models.TextField(default='', blank=True,
                            help_text='Код исследования (несколько кодов разделяются точкой с запятой без пробелов)')

    def __str__(self):
        return "%s" % self.title


class AutoAdd(models.Model):
    """
    Перечисление связей исследований, которые могут быть назначены только вместе (A только с B)
    """
    a = models.ForeignKey(Researches, help_text="Исследование, для которого устанавливается связь", db_index=True, related_name="a")
    b = models.ForeignKey(Researches, help_text="Исследование, которое должно быть назначено вместе", related_name="b")


class References(models.Model):
    """
    Справочник референсов
    """
    title = models.CharField(max_length=255, help_text='Название')
    about = models.TextField(help_text='Описание', blank=True)
    ref_m = JSONField(help_text='М')
    ref_f = JSONField(help_text='Ж')
    fraction = models.ForeignKey("Fractions", db_index=True, help_text='Фракция, к которой относится референс')

    def __str__(self):
        return str(self.fraction) + " | " + str(self.fraction) + " | " + self.title


class ResultVariants(models.Model):
    values = models.TextField(
        help_text='Варианты подсказок результатов, перечисленные через вертикальную черту без пробела "|"')

    def get_variants(self):
        return self.values.split('|')

    def __str__(self):
        return str(self.get_variants())


class MaterialVariants(models.Model):
    values = models.TextField(
        help_text='Варианты комментариев для материала, перечисленные через вертикальную черту без пробела "|"')

    def get_variants(self):
        return self.values.split('|')

    def __str__(self):
        return str(self.get_variants())


class Fractions(models.Model):
    """
    Фракции для исследований
    """
    title = models.CharField(max_length=255, help_text='Название фракции')
    research = models.ForeignKey(Researches, db_index=True, help_text='Исследование, к которому относится фракция')
    units = models.CharField(max_length=255, help_text='Еденицы измерения', blank=True, default='')
    default_ref = models.ForeignKey(References, help_text='Референс по-умолчанию', blank=True, null=True, default=None)
    ref_m = JSONField(help_text='Референсы (М)', blank=True)
    ref_f = JSONField(help_text='Референсы (Ж)', blank=True)
    relation = models.ForeignKey(ReleationsFT, help_text='Пробирка (пробирки)')
    uet_doc = models.FloatField(default=0, help_text='УЕТы для врача')
    uet_lab = models.FloatField(default=0, help_text='УЕТы для лаборанта')
    max_iterations = models.IntegerField(default=1, help_text='Максимальное число итераций')
    #type = models.IntegerField(default=-1, blank=True, null=True,
    #                           help_text='Варианты подсказок результатов (deprecated)')
    variants = models.ForeignKey(ResultVariants, null=True, blank=True, help_text='Варианты подсказок результатов')
    sort_weight = models.IntegerField(default=0, null=True, blank=True, help_text='Вес соритировки')
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие фракции')
    render_type = models.IntegerField(default=0, blank=True,
                                      help_text='Тип рендеринга (базовый тип (0) или динамическое число полей (1)')
    options = models.CharField(max_length=511, default="", blank=True,
                               help_text='Варианты для динамического числа полей')
    formula = models.TextField(default="", blank=True, help_text="Формула для автоматического вычисления значения")
    code = models.CharField(max_length=16, default='', blank=True, help_text='Код фракции')

    def __str__(self):
        return self.research.title + " | " + self.title


class Absorption(models.Model):
    """
    Поглощение
    """
    fupper = models.ForeignKey(Fractions, related_name="fupper", help_text='Какая фракция главнее')
    flower = models.ForeignKey(Fractions, related_name="flower", help_text='Какая фракция поглащяется главной')

    def __str__(self):
        return self.flower.__str__() + " -> " + self.fupper.__str__()


class AssignmentTemplate(models.Model):
    """
    Шаблоны назначений
    """
    user = models.ForeignKey(DoctorProfile, blank=True, null=True)
    researches = models.ManyToManyField(Researches)
