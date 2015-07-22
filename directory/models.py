from django.db import models
from podrazdeleniya.models import Subgroups
from jsonfield import JSONField
from researches.models import Tubes


class DirectionsGroup(models.Model):
    pass


class ReleationsFT(models.Model):
    tube = models.ForeignKey(Tubes)


class Researches(models.Model):
    direction = models.ForeignKey(DirectionsGroup)
    title = models.CharField(max_length=255)
    subgroup = models.ForeignKey(Subgroups)
    quota_oms = models.IntegerField()
    preparation = models.CharField(max_length=2047)


class Fractions(models.Model):
    title = models.CharField(max_length=255)
    research = models.ForeignKey(Researches)
    units = models.CharField(max_length=255)
    ref_m = JSONField()
    ref_f = JSONField()
    relation = models.ForeignKey(ReleationsFT)
    uet_doc = models.FloatField()
    uet_lab = models.FloatField()
