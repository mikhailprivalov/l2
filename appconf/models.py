from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Setting(models.Model):
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=500)
    value_type = models.CharField(max_length=1, choices=(('s', 'string'), ('i', 'integer'), ('b', 'boolean')))
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def actual_value(self):
        types = {
            's': str,
            'i': int,
            'b': (lambda v: v.lower().startswith('t') or v.startswith('1'))
        }
        return types[self.value_type](self.value)
