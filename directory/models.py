from django.db import models
from podrazdeleniya.models import Subgroups
from jsonfield import JSONField
from researches.models import Tubes


class DirectionsGroup(models.Model):
    pass


class ReleationsFT(models.Model):
    tube = models.ForeignKey(Tubes)


class Researches(models.Model):
    direction = models.ForeignKey(DirectionsGroup, null=True, blank=True)
    title = models.CharField(max_length=255, default="")
    subgroup = models.ForeignKey(Subgroups, related_name="subgroup")
    quota_oms = models.IntegerField(default=-1)
    preparation = models.CharField(max_length=2047, default="")
    edit_mode = models.IntegerField(
        default=0)  # 0 - Лаборант может сохранять и подтверждать. 1 - Лаборант сохраняет, врач должен подтвердить


class Fractions(models.Model):
    title = models.CharField(max_length=255)
    research = models.ForeignKey(Researches)
    units = models.CharField(max_length=255)
    ref_m = JSONField()
    ref_f = JSONField()
    relation = models.ForeignKey(ReleationsFT)
    uet_doc = models.FloatField(default=0)
    uet_lab = models.FloatField(default=0)
    max_iterations = models.IntegerField(default=1)
