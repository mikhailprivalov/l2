from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Setting(models.Model):
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=500)
    value_type = models.CharField(max_length=1, choices=(('s', 'string'), ('i', 'integer'),
                                                         ('f', 'float'), ('b', 'boolean')))

    def __str__(self):
        return "%s = %s (%s)" % (self.name, self.value, self.get_value_type_display())

    def actual_value(self):
        types = {
            's': str,
            'i': int,
            'b': (lambda v: v.lower().startswith('t') or v.startswith('1')),
            'f': float
        }
        return types[self.value_type](self.value)
