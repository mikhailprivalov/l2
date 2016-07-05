from django.db import models
from podrazdeleniya.models import Subgroups, Podrazdeleniya
from jsonfield import JSONField
from researches.models import Tubes


class DirectionsGroup(models.Model):
    """
    Группы направлений
    """
    pass


class ReleationsFT(models.Model):
    """
    (многие-ко-многим) фракции к пробиркам
    """
    tube = models.ForeignKey(Tubes)


class ResearchGroup(models.Model):
    title = models.CharField(max_length=63)
    lab = models.ForeignKey(Podrazdeleniya, null=True, blank=True)

    def __str__(self):
        return "%s" % self.title


class Researches(models.Model):
    """
    Вид исследования
    """
    direction = models.ForeignKey(DirectionsGroup, null=True, blank=True)
    title = models.CharField(max_length=255, default="")
    subgroup = models.ForeignKey(Subgroups, related_name="subgroup")
    quota_oms = models.IntegerField(default=-1)
    preparation = models.CharField(max_length=2047, default="")
    edit_mode = models.IntegerField(
        default=0)  # 0 - Лаборант может сохранять и подтверждать. 1 - Лаборант сохраняет, врач должен подтвердить
    hide = models.BooleanField(default=False, blank=True)
    no_attach = models.IntegerField(default=0, null=True, blank=True)
    sort_weight = models.IntegerField(default=0, null=True, blank=True)
    template = models.IntegerField(default=0, blank=True)
    comment_template = models.IntegerField(default=-1, null=True, blank=True)
    groups = models.ManyToManyField(ResearchGroup)

    def __str__(self):
        return "%s" % self.title


class Fractions(models.Model):
    """
    Фракции для исследований
    """
    title = models.CharField(max_length=255)
    research = models.ForeignKey(Researches, db_index=True)
    units = models.CharField(max_length=255)
    ref_m = JSONField()
    ref_f = JSONField()
    relation = models.ForeignKey(ReleationsFT)
    uet_doc = models.FloatField(default=0)
    uet_lab = models.FloatField(default=0)
    max_iterations = models.IntegerField(default=1)
    type = models.IntegerField(default=-1, blank=True, null=True)
    sort_weight = models.IntegerField(default=0, null=True, blank=True)
    hide = models.BooleanField(default=False, blank=True)
    render_type = models.IntegerField(default=0, blank=True)
    options = models.CharField(max_length=511, default="", blank=True)

    def __str__(self):
        return self.research.title + " | " + self.title


class Absorption(models.Model):
    """
    Поглощение
    """
    fupper = models.ForeignKey(Fractions, related_name="fupper")
    flower = models.ForeignKey(Fractions, related_name="flower")

    def __str__(self):
        return self.flower.__str__() + " -> " + self.fupper.__str__()


